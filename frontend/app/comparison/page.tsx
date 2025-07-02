"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { Loader2 } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import type { PerformanceData, PerformanceResult, ModelInfo } from "@/types"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { api } from "@/lib/api" // 引入真实的API模块

// Real API functions
const realApi = {
  getModels: async (): Promise<ModelInfo[]> => {
    const response = await api.get("/models")
    return response.data.models
  },
  startTest: async (data: { models: string[]; dataset: string }): Promise<{ task_id: string }> => {
    // 后端暂未实现此接口，我们先模拟
    console.log("Starting test with:", data)
    await new Promise((res) => setTimeout(res, 1000))
    return { task_id: `task_${Date.now()}` }
  },
  getTestResult: async (taskId: string): Promise<PerformanceResult> => {
    // 后端暂未实现此接口，我们先返回模拟数据
    console.log("Fetching result for:", taskId)
    await new Promise((res) => setTimeout(res, 1500))
    return {
      barChartData: [
        { name: "YOLO11n", FPS: 65, 精确度: 0.85, 召回率: 0.82, F1分数: 0.83, 推理时间: 15.4 },
        { name: "自定义人脸模型", FPS: 42, 精确度: 0.95, 召回率: 0.91, F1分数: 0.93, 推理时间: 23.8 },
        { name: "YOLOv8n", FPS: 75, 精确度: 0.88, 召回率: 0.84, F1分数: 0.86, 推理时间: 13.3 },
      ],
      radarChartData: [
        { subject: "FPS", YOLO11n: 0.65, 自定义人脸模型: 0.42, YOLOv8n: 0.75, fullMark: 1 },
        { subject: "精确度", YOLO11n: 0.85, 自定义人脸模型: 0.95, YOLOv8n: 0.88, fullMark: 1 },
        { subject: "召回率", YOLO11n: 0.82, 自定义人脸模型: 0.91, YOLOv8n: 0.84, fullMark: 1 },
        { subject: "F1分数", YOLO11n: 0.83, 自定义人脸模型: 0.93, YOLOv8n: 0.86, fullMark: 1 },
        { subject: "效率", YOLO11n: 0.87, 自定义人脸模型: 0.76, YOLOv8n: 0.92, fullMark: 1 },
      ],
    }
  },
}

const metricOptions = ["FPS", "精确度", "召回率", "F1分数", "推理时间"]
const datasetOptions = ["micro_wider验证集", "WIDER_val验证集"]
const modelColors = {
  YOLO11n: "hsl(var(--primary))",
  自定义人脸模型: "hsl(var(--success))",
  YOLOv8n: "hsl(var(--warning))",
}

export default function ComparisonPage() {
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([])
  const [selectedModels, setSelectedModels] = useState<string[]>([])
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(metricOptions)
  const [selectedDataset, setSelectedDataset] = useState<string>(datasetOptions[0])
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<PerformanceResult | null>(null)
  const { toast } = useToast()

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const models = await realApi.getModels()
      setAvailableModels(models)
        setSelectedModels(models.map(m => m.id))
      } catch (error) {
        toast({ title: "获取模型失败", description: "无法从后端获取模型列表。", variant: "destructive" })
      }
    }
    fetchModels()
  }, [toast])

  const handleTest = async () => {
    if (selectedModels.length === 0) {
      toast({ title: "请选择模型", description: "至少需要选择一个模型进行测试。", variant: "destructive" })
      return
    }
    setIsLoading(true)
    setResults(null)
    try {
      const { task_id } = await realApi.startTest({
        models: selectedModels,
        dataset: selectedDataset,
      })
      toast({ title: "测试已开始", description: `任务ID: ${task_id}` })
      const testResults = await realApi.getTestResult(task_id)
      setResults(testResults)
      toast({ title: "测试完成", description: "性能数据已更新。" })
    } catch (error) {
      toast({ title: "测试失败", description: "无法获取测试结果，请稍后重试。", variant: "destructive" })
    } finally {
      setIsLoading(false)
    }
  }

  const handleModelSelection = (model: string) => {
    setSelectedModels((prev) => (prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]))
  }

  const handleMetricSelection = (metric: string) => {
    setSelectedMetrics((prev) => (prev.includes(metric) ? prev.filter((m) => m !== metric) : [...prev, metric]))
  }

  const getBestValue = (metric: keyof PerformanceData) => {
    if (!results?.barChartData || results.barChartData.length === 0) return null
    const values = results.barChartData.map((d) => d[metric])
    return metric === "推理时间" ? Math.min(...values) : Math.max(...values)
  }

  return (
    <div className="container pt-24 pb-12">
      <div className="text-center mb-12">
        <h1 className="text-title-medium">模型性能对比</h1>
        <p className="text-body-large text-muted-foreground mt-2">选择模型、指标和数据集，开始进行性能分析。</p>
      </div>
      <div className="grid lg:grid-cols-12 gap-8">
        {/* Controls Panel */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>筛选控制</CardTitle>
              <CardDescription>配置您的性能测试</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>模型选择器 (多选)</Label>
                <div className="space-y-2">
                    {availableModels.map((model) => (
                    <div key={model.id} className="flex items-center space-x-2">
                      <Checkbox
                        id={model.id}
                        checked={selectedModels.includes(model.id)}
                        onCheckedChange={() => handleModelSelection(model.id)}
                      />
                      <label htmlFor={model.id} className="text-sm font-medium">
                        {model.name}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label>指标选择器</Label>
                <div className="grid grid-cols-2 gap-2">
                  {metricOptions.map((metric) => (
                    <div key={metric} className="flex items-center space-x-2">
                      <Checkbox
                        id={metric}
                        checked={selectedMetrics.includes(metric)}
                        onCheckedChange={() => handleMetricSelection(metric)}
                      />
                      <label htmlFor={metric} className="text-sm font-medium">
                        {metric}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label>数据集选择器</Label>
                <RadioGroup value={selectedDataset} onValueChange={setSelectedDataset}>
                  {datasetOptions.map((dataset) => (
                    <div key={dataset} className="flex items-center space-x-2">
                      <RadioGroupItem value={dataset} id={dataset} />
                      <Label htmlFor={dataset}>{dataset}</Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
              <Button onClick={handleTest} disabled={isLoading} className="w-full">
                {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {isLoading ? "测试中..." : "开始性能测试"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Data Display */}
        <div className="lg:col-span-9 space-y-8">
          {isLoading && !results && (
            <div className="flex flex-col items-center justify-center h-96 rounded-lg border border-dashed">
              <Loader2 className="h-16 w-16 animate-spin text-primary" />
              <p className="mt-4 text-muted-foreground">正在加载性能数据...</p>
            </div>
          )}
          {results && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>性能对比柱状图</CardTitle>
                </CardHeader>
                <CardContent>
                  <ChartContainer className="h-[400px] w-full" config={{}}>
                    <ResponsiveContainer>
                      <BarChart data={results.barChartData}>
                        <CartesianGrid vertical={false} />
                        <XAxis dataKey="name" tickLine={false} axisLine={false} tickMargin={8} />
                        <YAxis />
                        <Tooltip content={<ChartTooltipContent />} />
                        <Legend />
                        {selectedMetrics
                          .filter((m) => m !== "推理时间")
                          .map((metric) => (
                            <Bar
                              key={metric}
                              dataKey={metric}
                              fill={modelColors[metric as keyof typeof modelColors] || "#8884d8"}
                              radius={[4, 4, 0, 0]}
                            />
                          ))}
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>综合性能雷达图</CardTitle>
                </CardHeader>
                <CardContent>
                  <ChartContainer className="h-[400px] w-full" config={{}}>
                    <ResponsiveContainer>
                      <RadarChart cx="50%" cy="50%" outerRadius="80%" data={results.radarChartData}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="subject" />
                        <PolarRadiusAxis angle={30} domain={[0, 1]} />
                        <Tooltip content={<ChartTooltipContent />} />
                        <Legend />
                        {selectedModels.map((modelId) => {
                          const model = availableModels.find(m => m.id === modelId)
                          return model ? (
                          <Radar
                              key={model.id}
                              name={model.name}
                              dataKey={model.name}
                              stroke={modelColors[model.name as keyof typeof modelColors] || '#8884d8'}
                              fill={modelColors[model.name as keyof typeof modelColors] || '#8884d8'}
                            fillOpacity={0.6}
                          />
                          ) : null
                        })}
                      </RadarChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>详细数据表格</CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>模型名称</TableHead>
                        {metricOptions.map((metric) => (
                          <TableHead key={metric}>{metric}</TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {results.barChartData.map((row) => (
                        <TableRow key={row.name}>
                          <TableCell className="font-medium">{row.name}</TableCell>
                          {metricOptions.map((metric) => {
                            const key = metric as keyof PerformanceData
                            const value = row[key]
                            const bestValue = getBestValue(key)
                            const isBest = value === bestValue
                            return (
                              <TableCell key={metric} className={isBest ? "text-success font-bold" : ""}>
                                {value}
                              </TableCell>
                            )
                          })}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
