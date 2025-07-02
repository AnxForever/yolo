"use client"

import { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import {
  Line,
  LineChart,
  Pie,
  PieChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts"
import { ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import type { SystemStats, DatasetStats, TestHistory } from "@/types"
import { format, formatDistanceToNow, subDays } from "date-fns"
import { zhCN } from "date-fns/locale"
import { Button } from "@/components/ui/button"

// Mock API functions
const mockApi = {
  getSystemStats: async (): Promise<SystemStats> => {
    await new Promise((res) => setTimeout(res, 300))
    return {
      gpuUsage: Math.floor(Math.random() * 50 + 25), // 25-75%
      memoryUsage: {
        used: Math.round((Math.random() * 8 + 4) * 10) / 10, // 4.0-12.0 GB
        total: 16,
      },
      activeModels: 3,
      uptime: Math.floor(Math.random() * 1000000) + 86400, // 1 day to ~12 days
    }
  },
  getDatasetStats: async (): Promise<DatasetStats> => {
    await new Promise((res) => setTimeout(res, 500))
    return [
      {
        name: "micro_wider_val",
        imageCount: 3226,
        description: "WIDER FACE数据集的微型验证子集，用于快速测试。",
        lastUpdated: new Date().toISOString(),
        classDistribution: [{ name: "Face", value: 3226 }],
      },
      {
        name: "WIDER_val",
        imageCount: 16130,
        description: "标准WIDER FACE验证集，包含多种复杂场景。",
        lastUpdated: subDays(new Date(), 15).toISOString(),
        classDistribution: [{ name: "Face", value: 16130 }],
      },
    ]
  },
  getTestHistory: async (): Promise<TestHistory> => {
    await new Promise((res) => setTimeout(res, 800))
    return Array.from({ length: 50 }, (_, i) => ({
      id: `test_${i}`,
      testTime: subDays(new Date(), i * 2).toISOString(),
      models: [["YOLO11n", "YOLOv8n"], ["自定义人脸模型"]][i % 2],
      dataset: ["micro_wider_val", "WIDER_val"][i % 2],
      results: {
        fps: Math.floor(Math.random() * 30 + 50),
        accuracy: Math.round((Math.random() * 0.1 + 0.85) * 100) / 100,
      },
    }))
  },
}

const formatUptime = (seconds: number) => {
  const d = Math.floor(seconds / (3600 * 24))
  const h = Math.floor((seconds % (3600 * 24)) / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${d}天 ${h}小时 ${m}分钟`
}

export default function StatisticsPage() {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null)
  const [datasetStats, setDatasetStats] = useState<DatasetStats | null>(null)
  const [history, setHistory] = useState<TestHistory | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [currentPage, setCurrentPage] = useState(1)
  const ITEMS_PER_PAGE = 10

  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm])

  useEffect(() => {
    const fetchData = async () => {
      setSystemStats(await mockApi.getSystemStats())
      setDatasetStats(await mockApi.getDatasetStats())
      setHistory(await mockApi.getTestHistory())
    }
    fetchData()

    const interval = setInterval(async () => {
      setSystemStats(await mockApi.getSystemStats())
    }, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [])

  const filteredHistory = useMemo(() => {
    if (!history) return []
    return history.filter((item) => item.models.join(", ").toLowerCase().includes(searchTerm.toLowerCase()))
  }, [history, searchTerm])

  return (
    <div className="container pt-24 pb-12 space-y-12">
      <div className="text-center">
        <h1 className="text-title-medium">数据统计</h1>
        <p className="text-body-large text-muted-foreground mt-2">监控系统状态、数据集信息和历史测试记录。</p>
      </div>

      {/* System Status Dashboard */}
      <section>
        <h2 className="text-title-small mb-4">系统状态仪表板</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle>GPU 使用率</CardTitle>
            </CardHeader>
            <CardContent>
              <ChartContainer config={{}} className="h-40 w-full">
                <ResponsiveContainer>
                  <RadialBarChart
                    data={[{ name: "GPU", value: systemStats?.gpuUsage || 0 }]}
                    startAngle={90}
                    endAngle={-270}
                    innerRadius="70%"
                    outerRadius="100%"
                    barSize={20}
                  >
                    <RadialBar background dataKey="value" cornerRadius={10} fill="hsl(var(--primary))" />
                    <text
                      x="50%"
                      y="50%"
                      textAnchor="middle"
                      dominantBaseline="middle"
                      className="fill-foreground text-3xl font-bold"
                    >
                      {systemStats?.gpuUsage || 0}%
                    </text>
                  </RadialBarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>内存使用</CardTitle>
              <CardDescription>
                {systemStats?.memoryUsage.used.toFixed(1)} GB / {systemStats?.memoryUsage.total} GB
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Progress
                value={systemStats ? (systemStats.memoryUsage.used / systemStats.memoryUsage.total) * 100 : 0}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>活跃模型数</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-5xl font-bold">{systemStats?.activeModels || 0}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>系统运行时间</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xl font-semibold">{systemStats ? formatUptime(systemStats.uptime) : "..."}</p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Dataset Information */}
      <section>
        <h2 className="text-title-small mb-4">数据集信息</h2>
        <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
          {datasetStats?.map((dataset) => (
            <Card key={dataset.name}>
              <CardHeader>
                <CardTitle>{dataset.name}</CardTitle>
                <CardDescription>
                  最后更新: {formatDistanceToNow(new Date(dataset.lastUpdated), { addSuffix: true, locale: zhCN })}
                </CardDescription>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <p className="text-3xl font-bold">{dataset.imageCount.toLocaleString()}</p>
                  <p className="text-muted-foreground">图片数量</p>
                  <p className="text-sm">{dataset.description}</p>
                </div>
                <ChartContainer config={{}} className="h-40 w-full">
                  <ResponsiveContainer>
                    <PieChart>
                      <Pie
                        data={dataset.classDistribution}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={60}
                        fill="hsl(var(--primary))"
                        label
                      />
                      <Tooltip content={<ChartTooltipContent />} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartContainer>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Test History */}
      <section>
        <h2 className="text-title-small mb-4">测试历史记录</h2>
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle>历史记录</CardTitle>
                <CardDescription>查看和搜索过去的性能测试。</CardDescription>
              </div>
              <Input
                placeholder="按模型名称搜索..."
                className="max-w-sm"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>测试时间</TableHead>
                    <TableHead>测试模型</TableHead>
                    <TableHead>数据集</TableHead>
                    <TableHead>FPS</TableHead>
                    <TableHead>精确度</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredHistory
                    .slice((currentPage - 1) * ITEMS_PER_PAGE, currentPage * ITEMS_PER_PAGE)
                    .map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{format(new Date(item.testTime), "yyyy-MM-dd HH:mm")}</TableCell>
                        <TableCell>{item.models.join(", ")}</TableCell>
                        <TableCell>{item.dataset}</TableCell>
                        <TableCell>{item.results.fps}</TableCell>
                        <TableCell>{item.results.accuracy}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </div>
            <div className="flex items-center justify-end space-x-2 py-4">
              <span className="text-sm text-muted-foreground">
                Page {currentPage} of {Math.ceil(filteredHistory.length / ITEMS_PER_PAGE)}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((prev) => prev + 1)}
                disabled={currentPage >= Math.ceil(filteredHistory.length / ITEMS_PER_PAGE)}
              >
                Next
              </Button>
            </div>
            <div className="mt-6">
              <h3 className="text-lg font-semibold mb-2">性能趋势 (精确度)</h3>
              <ChartContainer config={{}} className="h-72 w-full">
                <ResponsiveContainer>
                  <LineChart data={history?.slice().reverse() || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="testTime" tickFormatter={(time) => format(new Date(time), "MM-dd")} />
                    <YAxis domain={[0.8, 1]} />
                    <Tooltip
                      content={({ active, payload, label }) =>
                        active && payload?.length ? (
                          <div className="p-2 border rounded-lg bg-background shadow-lg">
                            <p>{format(new Date(label), "yyyy-MM-dd")}</p>
                            <p className="text-primary">{`精确度: ${payload[0].value}`}</p>
                          </div>
                        ) : null
                      }
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="results.accuracy"
                      name="精确度"
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
