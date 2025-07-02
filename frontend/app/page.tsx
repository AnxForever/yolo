import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BarChartBig, Target, TrendingUp, Wrench } from "lucide-react"
import Link from "next/link"

const featureCards = [
  {
    icon: <BarChartBig className="h-8 w-8 text-primary" />,
    title: "模型性能对比",
    description: "多维度性能指标分析，直观的图表展示",
    href: "/comparison",
  },
  {
    icon: <Target className="h-8 w-8 text-primary" />,
    title: "实时检测演示",
    description: "上传图片，实时体验不同模型的检测效果",
    href: "/demo",
  },
  {
    icon: <TrendingUp className="h-8 w-8 text-primary" />,
    title: "详细数据分析",
    description: "系统性能监控，历史测试记录",
    href: "/statistics",
  },
  {
    icon: <Wrench className="h-8 w-8 text-primary" />,
    title: "技术架构",
    description: "基于YOLO和FastAPI的现代化架构",
    href: "/about",
  },
]

export default function HomePage() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Hero Section */}
      <section className="relative flex flex-col items-center justify-center h-screen text-center px-4 bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="z-10 space-y-6">
          <h1 className="text-title-large tracking-tighter">AI视觉模型性能对比平台</h1>
          <p className="text-title-small text-muted-foreground">专业的YOLO模型测试与分析工具</p>
          <p className="max-w-2xl mx-auto text-body-large text-muted-foreground">
            支持多种YOLO模型性能对比，实时检测演示，详细数据分析
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button asChild size="lg">
              <Link href="/comparison">开始测试</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/demo">查看演示</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-gray-50">
        <div className="container">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {featureCards.map((card) => (
              <Link href={card.href} key={card.title}>
                <Card className="h-full hover:border-primary transition-colors duration-300 hover:shadow-lg hover:-translate-y-1 bg-white">
                  <CardHeader className="flex flex-row items-center gap-4">
                    {card.icon}
                    <CardTitle>{card.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription>{card.description}</CardDescription>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
