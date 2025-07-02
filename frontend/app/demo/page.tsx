"use client"

import { useState, useMemo, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useToast } from "@/components/ui/use-toast"
import { Upload, ImageIcon, X, Loader2, Sparkles, Monitor } from "lucide-react"
import Image from "next/image"
import type { DetectionResult, Detection } from "@/types"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import { ChartContainer } from "@/components/ui/chart"

const presetImages = [
  { name: "Faces", url: "/placeholder.svg?height=400&width=600" },
  { name: "Vehicles", url: "/placeholder.svg?height=400&width=600" },
  { name: "Animals", url: "/placeholder.svg?height=400&width=600" },
  { name: "Objects", url: "/placeholder.svg?height=400&width=600" },
]

// 性能监控相关的接口和函数
interface PerformanceMetrics {
  timestamp: number
  fps: number
  memoryUsage: number
  cpuUsage: number
  detectionTime: number
  frameProcessingTime: number
}

interface SystemInfo {
  totalMemory: number
  availableMemory: number
  usedMemory: number
  memoryUsagePercent: number
  cpuCores: number
  platform: string
  userAgent: string
}

// 性能监控 Hook
const usePerformanceMonitor = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics[]>([])
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [isMonitoring, setIsMonitoring] = useState(false)
  const monitoringInterval = useRef<NodeJS.Timeout | null>(null)
  const frameCount = useRef(0)
  const lastFrameTime = useRef(performance.now())

  // 获取系统信息
  const getSystemInfo = async (): Promise<SystemInfo> => {
    // 获取内存信息（如果支持）
    let memoryInfo = { totalJSHeapSize: 0, usedJSHeapSize: 0, jsHeapSizeLimit: 0 }
    if ("memory" in performance) {
      memoryInfo = (performance as any).memory
    }

    // 获取硬件信息
    const hardwareConcurrency = navigator.hardwareConcurrency || 4

    return {
      totalMemory: memoryInfo.jsHeapSizeLimit || 0,
      availableMemory: memoryInfo.totalJSHeapSize || 0,
      usedMemory: memoryInfo.usedJSHeapSize || 0,
      memoryUsagePercent: memoryInfo.jsHeapSizeLimit
        ? (memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit) * 100
        : 0,
      cpuCores: hardwareConcurrency,
      platform: navigator.platform,
      userAgent: navigator.userAgent,
    }
  }

  // 计算FPS
  const updateFPS = () => {
    frameCount.current++
    const now = performance.now()
    const delta = now - lastFrameTime.current

    if (delta >= 1000) {
      // 每秒更新一次
      const fps = Math.round((frameCount.current * 1000) / delta)
      frameCount.current = 0
      lastFrameTime.current = now
      return fps
    }
    return null
  }

  // 模拟CPU使用率（实际应用中需要后端提供）
  const getCPUUsage = (): number => {
    // 基于当前性能指标模拟CPU使用率
    const baseUsage = 20 + Math.random() * 30 // 20-50% 基础使用率
    const detectionLoad = metrics.length > 0 ? metrics[metrics.length - 1]?.detectionTime / 10 : 0
    return Math.min(100, baseUsage + detectionLoad)
  }

  const startMonitoring = async () => {
    setIsMonitoring(true)
    const sysInfo = await getSystemInfo()
    setSystemInfo(sysInfo)

    monitoringInterval.current = setInterval(async () => {
      const fps = updateFPS() || 0
      const currentSysInfo = await getSystemInfo()
      const cpuUsage = getCPUUsage()

      const newMetric: PerformanceMetrics = {
        timestamp: Date.now(),
        fps,
        memoryUsage: currentSysInfo.memoryUsagePercent,
        cpuUsage,
        detectionTime: 0, // 将在检测时更新
        frameProcessingTime: performance.now() % 100, // 模拟帧处理时间
      }

      setMetrics((prev) => {
        const updated = [...prev, newMetric]
        // 只保留最近50个数据点
        return updated.slice(-50)
      })
      setSystemInfo(currentSysInfo)
    }, 1000)
  }

  const stopMonitoring = () => {
    setIsMonitoring(false)
    if (monitoringInterval.current) {
      clearInterval(monitoringInterval.current)
      monitoringInterval.current = null
    }
  }

  const updateDetectionTime = (detectionTime: number) => {
    setMetrics((prev) => {
      if (prev.length === 0) return prev
      const updated = [...prev]
      updated[updated.length - 1].detectionTime = detectionTime
      return updated
    })
  }

  const clearMetrics = () => {
    setMetrics([])
  }

  return {
    metrics,
    systemInfo,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    updateDetectionTime,
    clearMetrics,
  }
}

// 摄像头相关的 hook 和函数
const useCameraStream = () => {
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
      })
      setStream(mediaStream)
      setIsStreaming(true)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
    } catch (error) {
      console.error("Error accessing camera:", error)
      throw new Error("无法访问摄像头，请检查权限设置")
    }
  }

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      setStream(null)
      setIsStreaming(false)
    }
  }

  const captureFrame = (): Promise<File> => {
    return new Promise((resolve, reject) => {
      if (!videoRef.current || !canvasRef.current) {
        reject(new Error("Video or canvas not available"))
        return
      }

      const canvas = canvasRef.current
      const video = videoRef.current
      const ctx = canvas.getContext("2d")

      if (!ctx) {
        reject(new Error("Canvas context not available"))
        return
      }

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      ctx.drawImage(video, 0, 0)

      canvas.toBlob(
        (blob) => {
          if (blob) {
            const file = new File([blob], `camera_capture_${Date.now()}.jpg`, { type: "image/jpeg" })
            resolve(file)
          } else {
            reject(new Error("Failed to capture frame"))
          }
        },
        "image/jpeg",
        0.9,
      )
    })
  }

  return { stream, isStreaming, videoRef, canvasRef, startCamera, stopCamera, captureFrame }
}

// 模型列表 - 设计为可扩展的结构，便于后端集成
const models = [
  { id: "yolo11n", name: "YOLO11n", description: "通用快速模型", size: "6.2MB" },
  { id: "yolo11s", name: "YOLO11s", description: "平衡性能与速度", size: "21.5MB" },
  { id: "yolo11m", name: "YOLO11m", description: "中等精度模型", size: "49.7MB" },
  { id: "face_model", name: "自定义人脸模型", description: "专为人脸检测优化", size: "12.3MB" },
  { id: "yolov8n", name: "YOLOv8n", description: "上一代快速模型", size: "6.0MB" },
  { id: "yolov8s", name: "YOLOv8s", description: "上一代平衡模型", size: "21.2MB" },
]

// 检测间隔选项
const detectionIntervals = [
  { value: 500, label: "0.5秒 (2 FPS)", description: "最快检测" },
  { value: 1000, label: "1秒 (1 FPS)", description: "快速检测" },
  { value: 2000, label: "2秒 (0.5 FPS)", description: "标准检测" },
  { value: 3000, label: "3秒 (0.33 FPS)", description: "节能检测" },
  { value: 5000, label: "5秒 (0.2 FPS)", description: "低频检测" },
]

// Helper function to draw detections on a canvas
const drawDetectionsOnCanvas = (imageUrl: string, detections: Detection[]): Promise<string> => {
  return new Promise((resolve, reject) => {
    const img = new window.Image()
    img.crossOrigin = "anonymous"
    img.onload = () => {
      const canvas = document.createElement("canvas")
      canvas.width = img.naturalWidth
      canvas.height = img.naturalHeight
      const ctx = canvas.getContext("2d")
      if (!ctx) {
        return reject(new Error("Could not get canvas context"))
      }

      ctx.drawImage(img, 0, 0)

      // 定义不同类别的颜色
      const colors = {
        person: "#2196F3",
        car: "#4CAF50",
        cat: "#FF9800",
        dog: "#9C27B0",
        bicycle: "#F44336",
        default: "#2196F3",
      }

      detections.forEach((detection) => {
        const [x1, y1, x2, y2] = detection.box
        const label = `${detection.label} ${(detection.confidence * 100).toFixed(1)}%`
        const color = colors[detection.label as keyof typeof colors] || colors.default

        // 绘制边界框
        ctx.strokeStyle = color
        ctx.lineWidth = Math.max(2, canvas.width / 300)
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1)

        // 绘制标签背景和文字
        const fontSize = Math.max(14, canvas.width / 50)
        ctx.font = `bold ${fontSize}px sans-serif`
        const textWidth = ctx.measureText(label).width

        // 标签背景
        ctx.fillStyle = color
        ctx.fillRect(x1 - ctx.lineWidth / 2, y1 - fontSize - 8, textWidth + 8, fontSize + 8)

        // 标签文字
        ctx.fillStyle = "white"
        ctx.fillText(label, x1 + 4, y1 - 5)
      })

      resolve(canvas.toDataURL("image/jpeg", 0.9))
    }
    img.onerror = (err) => reject(err)
    img.src = imageUrl
  })
}

// Mock API function - 设计为与后端API兼容的结构
const mockDetectImage = async (formData: FormData): Promise<DetectionResult> => {
  const file = formData.get("image") as File
  const model = formData.get("model") as string
  const confidence = Number.parseFloat(formData.get("confidence") as string)
  const nms = Number.parseFloat(formData.get("nms") as string)
  const originalImageUrl = URL.createObjectURL(file)

  // 模拟网络延迟
  await new Promise((res) => setTimeout(res, 1500))

  const img = await new Promise<HTMLImageElement>((resolve) => {
    const image = new window.Image()
    image.onload = () => resolve(image)
    image.src = originalImageUrl
  })

  // 根据模型类型生成不同的检测结果
  const getDetectionsByModel = (modelId: string) => {
    const baseDetections = Math.floor(Math.random() * 8) + 3
    const labels = modelId === "face_model" ? ["person"] : ["person", "car", "cat", "dog", "bicycle"]

    return Array.from({ length: baseDetections }, () => {
      const width = (Math.random() * 0.2 + 0.1) * img.naturalWidth
      const height = (Math.random() * 0.3 + 0.15) * img.naturalHeight
      const x1 = Math.random() * (img.naturalWidth - width)
      const y1 = Math.random() * (img.naturalHeight - height)

      return {
        box: [x1, y1, x1 + width, y1 + height] as [number, number, number, number],
        label: labels[Math.floor(Math.random() * labels.length)],
        confidence: Math.random() * (0.95 - confidence) + confidence, // 基于置信度阈值
      }
    })
      .filter((d) => d.confidence >= confidence) // 过滤低置信度检测
      .sort((a, b) => b.confidence - a.confidence)
  }

  const detections = getDetectionsByModel(model)
  const resultImageUrl = await drawDetectionsOnCanvas(originalImageUrl, detections)

  // 根据模型性能特征模拟推理时间
  const modelPerformance = {
    yolo11n: { baseTime: 15, variance: 5 },
    yolo11s: { baseTime: 25, variance: 8 },
    yolo11m: { baseTime: 45, variance: 12 },
    face_model: { baseTime: 20, variance: 6 },
    yolov8n: { baseTime: 18, variance: 6 },
    yolov8s: { baseTime: 28, variance: 9 },
  }

  const perf = modelPerformance[model as keyof typeof modelPerformance] || modelPerformance.yolo11n
  const inferenceTime = Math.round(perf.baseTime + (Math.random() - 0.5) * perf.variance)

  return {
    originalImageUrl,
    resultImageUrl,
    metrics: {
      inferenceTime,
      fps: Math.round(1000 / inferenceTime),
      detectedObjects: detections.length,
    },
    detections,
  }
}

// 格式化内存大小
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

export default function DemoPage() {
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState(models[0].id)
  const [confidence, setConfidence] = useState([0.5])
  const [nms, setNms] = useState([0.4])
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<DetectionResult | null>(null)
  const { toast } = useToast()

  const [activeTab, setActiveTab] = useState("upload")
  const [isRealTimeDetection, setIsRealTimeDetection] = useState(false)
  const [detectionInterval, setDetectionInterval] = useState<NodeJS.Timeout | null>(null)
  const camera = useCameraStream()
  const performanceMonitor = usePerformanceMonitor()

  const [detectionIntervalMs, setDetectionIntervalMs] = useState(2000) // 默认2秒
  const [frameSkip, setFrameSkip] = useState(1) // 帧跳过数量
  const [performanceMode, setPerformanceMode] = useState<"quality" | "balanced" | "performance">("balanced")
  const [detectionStats, setDetectionStats] = useState({
    totalDetections: 0,
    averageTime: 0,
    lastDetectionTime: 0,
  })

  // 当摄像头开启时自动开始性能监控
  useEffect(() => {
    if (camera.isStreaming) {
      performanceMonitor.startMonitoring()
    } else {
      performanceMonitor.stopMonitoring()
    }

    return () => {
      performanceMonitor.stopMonitoring()
    }
  }, [camera.isStreaming])

  const handleFileChange = (file: File | null) => {
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        toast({ title: "文件过大", description: "请上传小于10MB的图片。", variant: "destructive" })
        return
      }
      setImageFile(file)
      setPreviewUrl(URL.createObjectURL(file))
      setResult(null)
    }
  }

  const handlePresetSelect = async (url: string, name: string) => {
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      const file = new File([blob], `${name.toLowerCase().replace(" ", "_")}.jpg`, { type: "image/jpeg" })
      handleFileChange(file)
    } catch (error) {
      toast({ title: "加载预设图片失败", variant: "destructive" })
    }
  }

  const clearImage = () => {
    setImageFile(null)
    setPreviewUrl(null)
    setResult(null)
  }

  const handleDetect = async () => {
    if (!imageFile) {
      toast({ title: "未选择图片", description: "请先上传一张图片。", variant: "destructive" })
      return
    }
    setIsLoading(true)
    setResult(null)

    const startTime = performance.now()

    // 构建与后端API兼容的FormData
    const formData = new FormData()
    formData.append("image", imageFile)
    formData.append("model", selectedModel)
    formData.append("confidence", String(confidence[0]))
    formData.append("nms", String(nms[0]))

    try {
      const detectionResult = await mockDetectImage(formData)
      const endTime = performance.now()
      const detectionTime = endTime - startTime

      // 更新性能监控
      performanceMonitor.updateDetectionTime(detectionTime)

      setResult(detectionResult)
      toast({ title: "检测成功", description: `检测到 ${detectionResult.metrics.detectedObjects} 个目标。` })
    } catch (error) {
      console.error("Detection failed:", error)
      toast({ title: "检测失败", description: "无法处理图片，请重试。", variant: "destructive" })
    } finally {
      setIsLoading(false)
    }
  }

  const handleCameraCapture = async () => {
    try {
      const capturedFile = await camera.captureFrame()
      handleFileChange(capturedFile)
      toast({ title: "拍照成功", description: "图片已捕获，可以开始检测。" })
    } catch (error) {
      toast({ title: "拍照失败", description: "无法捕获摄像头画面。", variant: "destructive" })
    }
  }

  const startRealTimeDetection = async () => {
    if (!camera.isStreaming) {
      toast({ title: "请先开启摄像头", variant: "destructive" })
      return
    }

    setIsRealTimeDetection(true)
    setDetectionStats({ totalDetections: 0, averageTime: 0, lastDetectionTime: 0 })

    let frameCount = 0
    let totalDetectionTime = 0
    let detectionCount = 0

    const detectLoop = async () => {
      frameCount++

      // 根据帧跳过设置决定是否进行检测
      if (frameCount % frameSkip !== 0) {
        return
      }

      const startTime = performance.now()

      try {
        const capturedFile = await camera.captureFrame()

        const formData = new FormData()
        formData.append("image", capturedFile)
        formData.append("model", selectedModel)
        formData.append("confidence", String(confidence[0]))
        formData.append("nms", String(nms[0]))

        // 根据性能模式调整图片质量
        const quality = performanceMode === "performance" ? 0.6 : performanceMode === "balanced" ? 0.8 : 0.9
        formData.append("quality", String(quality))

        const detectionResult = await mockDetectImage(formData)
        setResult(detectionResult)

        const endTime = performance.now()
        const detectionTime = endTime - startTime
        totalDetectionTime += detectionTime
        detectionCount++

        // 更新性能监控
        performanceMonitor.updateDetectionTime(detectionTime)

        setDetectionStats({
          totalDetections: detectionCount,
          averageTime: Math.round(totalDetectionTime / detectionCount),
          lastDetectionTime: Math.round(detectionTime),
        })
      } catch (error) {
        console.error("Real-time detection error:", error)
      }
    }

    // 使用用户设置的检测间隔
    const interval = setInterval(detectLoop, detectionIntervalMs)
    setDetectionInterval(interval)
  }

  const stopRealTimeDetection = () => {
    setIsRealTimeDetection(false)
    if (detectionInterval) {
      clearInterval(detectionInterval)
      setDetectionInterval(null)
    }
  }

  const handleStartCamera = async () => {
    try {
      await camera.startCamera()
      toast({ title: "摄像头已开启", description: "可以开始实时检测了。" })
    } catch (error) {
      toast({ title: "摄像头启动失败", description: error.message, variant: "destructive" })
    }
  }

  const handleStopCamera = () => {
    camera.stopCamera()
    stopRealTimeDetection()
    setResult(null)
    toast({ title: "摄像头已关闭" })
  }

  const selectedModelInfo = models.find((m) => m.id === selectedModel)

  const ImageUploader = useMemo(
    () => (
      <div
        className="relative border-2 border-dashed border-muted rounded-lg p-6 text-center cursor-pointer hover:border-primary transition-colors bg-gray-50"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          handleFileChange(e.dataTransfer.files[0])
        }}
      >
        <input
          type="file"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          accept=".jpg,.jpeg,.png"
          onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
        />
        {previewUrl ? (
          <>
            <Image
              src={previewUrl || "/placeholder.svg"}
              alt="Preview"
              width={200}
              height={150}
              className="mx-auto rounded-md object-contain h-36"
            />
            <Button variant="ghost" size="icon" className="absolute top-2 right-2" onClick={clearImage}>
              <X className="h-4 w-4" />
            </Button>
          </>
        ) : (
          <div className="flex flex-col items-center gap-2 text-muted-foreground">
            <Upload className="h-8 w-8" />
            <p>拖拽图片至此或点击上传</p>
            <p className="text-xs">支持 JPG, PNG, JPEG, 最大 10MB</p>
          </div>
        )}
      </div>
    ),
    [previewUrl],
  )

  return (
    <div className="container pt-24 pb-12 bg-gray-50 min-h-screen">
      <div className="text-center mb-12">
        <h1 className="text-title-medium">实时检测演示</h1>
        <p className="text-body-large text-muted-foreground mt-2">上传图片，体验不同模型的检测效果。</p>
      </div>
      <div className="grid lg:grid-cols-12 gap-8">
        {/* Controls Panel */}
        <div className="lg:col-span-4 space-y-6">
          <Card className="bg-white">
            <CardHeader>
              <CardTitle>1. 选择输入方式</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="upload">图片上传</TabsTrigger>
                  <TabsTrigger value="camera">实时摄像头</TabsTrigger>
                </TabsList>

                <TabsContent value="upload" className="mt-4">
                  {ImageUploader}
                  <p className="text-sm text-muted-foreground mt-4 mb-2 text-center">或选择预设图片</p>
                  <div className="grid grid-cols-2 gap-2">
                    {presetImages.map((img) => (
                      <button
                        key={img.name}
                        onClick={() => handlePresetSelect(img.url, img.name)}
                        className="rounded-md overflow-hidden relative group"
                      >
                        <Image
                          src={img.url || "/placeholder.svg"}
                          alt={img.name}
                          width={150}
                          height={100}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/50 flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity">
                          {img.name}
                        </div>
                      </button>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="camera" className="mt-4">
                  <div className="space-y-4">
                    <div className="relative border-2 border-dashed border-muted rounded-lg p-4 text-center bg-gray-50">
                      {!camera.isStreaming ? (
                        <div className="flex flex-col items-center gap-4 py-8">
                          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                            <svg className="h-8 w-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                              />
                            </svg>
                          </div>
                          <p className="text-muted-foreground">点击开启摄像头进行实时检测</p>
                          <Button onClick={handleStartCamera}>开启摄像头</Button>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <video
                            ref={camera.videoRef}
                            autoPlay
                            playsInline
                            muted
                            className="w-full max-w-md mx-auto rounded-lg"
                          />
                          <canvas ref={camera.canvasRef} className="hidden" />
                          <div className="flex gap-2 justify-center">
                            <Button onClick={handleCameraCapture} variant="outline">
                              拍照检测
                            </Button>
                            <Button
                              onClick={isRealTimeDetection ? stopRealTimeDetection : startRealTimeDetection}
                              variant={isRealTimeDetection ? "destructive" : "default"}
                            >
                              {isRealTimeDetection ? "停止实时检测" : "开始实时检测"}
                            </Button>
                            <Button onClick={handleStopCamera} variant="outline">
                              关闭摄像头
                            </Button>
                          </div>
                          {isRealTimeDetection && (
                            <p className="text-sm text-muted-foreground">
                              实时检测中... 每{detectionIntervalMs / 1000}秒更新一次结果 (
                              {performanceMode === "quality"
                                ? "质量优先"
                                : performanceMode === "balanced"
                                  ? "平衡模式"
                                  : "性能优先"}
                              )
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <Card className="bg-white">
            <CardHeader>
              <CardTitle>2. 选择模型与参数</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>检测模型</Label>
                <Select value={selectedModel} onValueChange={setSelectedModel}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择模型" />
                  </SelectTrigger>
                  <SelectContent>
                    {models.map((model) => (
                      <SelectItem key={model.id} value={model.id}>
                        <div className="flex flex-col">
                          <span className="font-medium">{model.name}</span>
                          <span className="text-xs text-muted-foreground">
                            {model.description} • {model.size}
                          </span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {selectedModelInfo && (
                  <p className="text-sm text-muted-foreground">
                    {selectedModelInfo.description} • 模型大小: {selectedModelInfo.size}
                  </p>
                )}
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <Label>置信度阈值</Label>
                  <span className="text-sm font-mono">{confidence[0].toFixed(2)}</span>
                </div>
                <Slider value={confidence} onValueChange={setConfidence} max={1} min={0.1} step={0.05} />
                <p className="text-xs text-muted-foreground mt-1">只显示置信度高于此值的检测结果</p>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <Label>NMS阈值</Label>
                  <span className="text-sm font-mono">{nms[0].toFixed(2)}</span>
                </div>
                <Slider value={nms} onValueChange={setNms} max={1} min={0.1} step={0.05} />
                <p className="text-xs text-muted-foreground mt-1">非极大值抑制阈值，用于去除重复检测</p>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white">
            <CardHeader>
              <CardTitle>3. 性能控制</CardTitle>
              <CardDescription>调整检测频率和性能模式</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>检测间隔</Label>
                <Select
                  value={String(detectionIntervalMs)}
                  onValueChange={(value) => setDetectionIntervalMs(Number(value))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="选择检测间隔" />
                  </SelectTrigger>
                  <SelectContent>
                    {detectionIntervals.map((interval) => (
                      <SelectItem key={interval.value} value={String(interval.value)}>
                        <div className="flex flex-col">
                          <span className="font-medium">{interval.label}</span>
                          <span className="text-xs text-muted-foreground">{interval.description}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>性能模式</Label>
                <Select
                  value={performanceMode}
                  onValueChange={(value: "quality" | "balanced" | "performance") => setPerformanceMode(value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="quality">
                      <div className="flex flex-col">
                        <span className="font-medium">质量优先</span>
                        <span className="text-xs text-muted-foreground">最高画质，较慢速度</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="balanced">
                      <div className="flex flex-col">
                        <span className="font-medium">平衡模式</span>
                        <span className="text-xs text-muted-foreground">平衡画质与速度</span>
                      </div>
                    </SelectItem>
                    <SelectItem value="performance">
                      <div className="flex flex-col">
                        <span className="font-medium">性能优先</span>
                        <span className="text-xs text-muted-foreground">最快速度，较低画质</span>
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <Label>帧跳过数量</Label>
                  <span className="text-sm font-mono">{frameSkip}</span>
                </div>
                <Slider
                  value={[frameSkip]}
                  onValueChange={(value) => setFrameSkip(value[0])}
                  max={10}
                  min={1}
                  step={1}
                />
                <p className="text-xs text-muted-foreground mt-1">每 {frameSkip} 帧检测一次，数值越大越节省资源</p>
              </div>

              {isRealTimeDetection && (
                <div className="p-3 bg-blue-50 rounded-lg border">
                  <h4 className="font-medium text-sm mb-2">实时统计</h4>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-muted-foreground">总检测次数:</span>
                      <span className="ml-1 font-mono">{detectionStats.totalDetections}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">平均耗时:</span>
                      <span className="ml-1 font-mono">{detectionStats.averageTime}ms</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">上次耗时:</span>
                      <span className="ml-1 font-mono">{detectionStats.lastDetectionTime}ms</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">检测频率:</span>
                      <span className="ml-1 font-mono">{(1000 / detectionIntervalMs).toFixed(1)} FPS</span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 性能监控面板 */}
          {performanceMonitor.isMonitoring && (
            <Card className="bg-white">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Monitor className="h-5 w-5" />
                  系统性能监控
                </CardTitle>
                <CardDescription>实时系统资源使用情况</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 系统信息 */}
                {performanceMonitor.systemInfo && (
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <Label className="text-sm">内存使用率</Label>
                        <span className="text-sm font-mono">
                          {performanceMonitor.systemInfo.memoryUsagePercent.toFixed(1)}%
                        </span>
                      </div>
                      <Progress value={performanceMonitor.systemInfo.memoryUsagePercent} className="h-2" />
                      <p className="text-xs text-muted-foreground mt-1">
                        {formatBytes(performanceMonitor.systemInfo.usedMemory)} /{" "}
                        {formatBytes(performanceMonitor.systemInfo.totalMemory)}
                      </p>
                    </div>

                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <Label className="text-sm">CPU 使用率</Label>
                        <span className="text-sm font-mono">
                          {performanceMonitor.metrics.length > 0
                            ? performanceMonitor.metrics[performanceMonitor.metrics.length - 1]?.cpuUsage.toFixed(1)
                            : 0}
                          %
                        </span>
                      </div>
                      <Progress
                        value={
                          performanceMonitor.metrics.length > 0
                            ? performanceMonitor.metrics[performanceMonitor.metrics.length - 1]?.cpuUsage
                            : 0
                        }
                        className="h-2"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        {performanceMonitor.systemInfo.cpuCores} 核心处理器
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <span className="text-muted-foreground">当前FPS:</span>
                        <span className="ml-1 font-mono">
                          {performanceMonitor.metrics.length > 0
                            ? performanceMonitor.metrics[performanceMonitor.metrics.length - 1]?.fps || 0
                            : 0}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">平台:</span>
                        <span className="ml-1 font-mono text-xs">{performanceMonitor.systemInfo.platform}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* 性能趋势图 */}
                {performanceMonitor.metrics.length > 5 && (
                  <div className="mt-4">
                    <Label className="text-sm mb-2 block">性能趋势</Label>
                    <ChartContainer config={{}} className="h-32 w-full">
                      <ResponsiveContainer>
                        <LineChart data={performanceMonitor.metrics.slice(-20)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="timestamp"
                            tickFormatter={(time) => new Date(time).toLocaleTimeString().slice(-8, -3)}
                            fontSize={10}
                          />
                          <YAxis fontSize={10} />
                          <Tooltip
                            labelFormatter={(time) => new Date(time).toLocaleTimeString()}
                            formatter={(value, name) => [
                              typeof value === "number" ? value.toFixed(1) : value,
                              name === "cpuUsage"
                                ? "CPU使用率(%)"
                                : name === "memoryUsage"
                                  ? "内存使用率(%)"
                                  : name === "fps"
                                    ? "FPS"
                                    : name,
                            ]}
                          />
                          <Line
                            type="monotone"
                            dataKey="cpuUsage"
                            stroke="#2196F3"
                            strokeWidth={2}
                            dot={false}
                            name="CPU使用率"
                          />
                          <Line
                            type="monotone"
                            dataKey="memoryUsage"
                            stroke="#4CAF50"
                            strokeWidth={2}
                            dot={false}
                            name="内存使用率"
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </ChartContainer>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={performanceMonitor.clearMetrics}
                    className="text-xs bg-transparent"
                  >
                    清除数据
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <Button
            size="lg"
            className="w-full"
            disabled={
              (activeTab === "upload" && !imageFile) || isLoading || (activeTab === "camera" && isRealTimeDetection)
            }
            onClick={activeTab === "upload" ? handleDetect : handleCameraCapture}
          >
            {isLoading ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : <Sparkles className="mr-2 h-5 w-5" />}
            {isLoading ? "正在检测..." : activeTab === "upload" ? "开始检测" : "拍照并检测"}
          </Button>
        </div>

        {/* Results Panel */}
        <div className="lg:col-span-8">
          <Card className="h-full bg-white">
            <CardHeader>
              <CardTitle>检测结果</CardTitle>
            </CardHeader>
            <CardContent>
              {!result && !isLoading && (
                <div className="flex flex-col items-center justify-center h-[600px] text-muted-foreground border border-dashed rounded-lg bg-gray-50">
                  <ImageIcon className="h-16 w-16 mb-4" />
                  <p>检测结果将在此处显示</p>
                </div>
              )}
              {isLoading && (
                <div className="flex flex-col items-center justify-center h-[600px] text-muted-foreground border border-dashed rounded-lg bg-gray-50">
                  <Loader2 className="h-16 w-16 mb-4 animate-spin text-primary" />
                  <p>正在分析图像，请稍候...</p>
                </div>
              )}
              {result && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label className="text-center block mb-2">原始图片</Label>
                      <Image
                        src={result.originalImageUrl || "/placeholder.svg"}
                        alt="Original"
                        width={600}
                        height={400}
                        className="rounded-lg w-full object-contain border"
                      />
                    </div>
                    <div>
                      <Label className="text-center block mb-2">检测结果</Label>
                      <Image
                        src={result.resultImageUrl || "/placeholder.svg"}
                        alt="Detection Result"
                        width={600}
                        height={400}
                        className="rounded-lg w-full object-contain border"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-2xl text-primary">{result.metrics.inferenceTime}ms</CardTitle>
                        <CardDescription>推理时间</CardDescription>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-2xl text-success">{result.metrics.fps}</CardTitle>
                        <CardDescription>FPS</CardDescription>
                      </CardHeader>
                    </Card>
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-2xl text-warning">{result.metrics.detectedObjects}</CardTitle>
                        <CardDescription>检测数量</CardDescription>
                      </CardHeader>
                    </Card>
                  </div>
                  <div>
                    <Label>详细信息</Label>
                    <div className="border rounded-lg max-h-60 overflow-y-auto mt-2">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>类别</TableHead>
                            <TableHead>置信度</TableHead>
                            <TableHead>位置 (x1, y1, x2, y2)</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {result.detections.map((d, i) => (
                            <TableRow key={i}>
                              <TableCell className="font-medium">{d.label}</TableCell>
                              <TableCell>{(d.confidence * 100).toFixed(1)}%</TableCell>
                              <TableCell className="font-mono text-xs">{`[${d.box.map((v) => v.toFixed(0)).join(", ")}]`}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
