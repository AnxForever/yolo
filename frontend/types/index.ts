export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  size: string;
  type: string;
  supported_classes: string[];
  performance: {
    avg_inference_time: number;
    avg_fps: number;
  };
  loaded?: boolean;
}

export interface PerformanceData {
  name: string;
  FPS: number;
  "精确度": number;
  "召回率": number;
  "F1分数": number;
  "推理时间": number;
}

export interface RadarData {
  subject: string;
  [modelName: string]: string | number;
  fullMark: number;
}

export interface PerformanceResult {
  barChartData: PerformanceData[];
  radarChartData: RadarData[];
}

export interface Detection {
  box: [number, number, number, number] // [x1, y1, x2, y2]
  label: string
  confidence: number
}

export interface DetectionMetrics {
  inferenceTime: number // in ms
  fps: number
  detectedObjects: number
}

export interface DetectionResult {
  originalImageUrl: string
  resultImageUrl: string
  metrics: DetectionMetrics
  detections: Detection[]
}

// New types for Statistics page
export interface SystemStats {
  gpuUsage: number // 0-100
  memoryUsage: {
    used: number // GB
    total: number // GB
  }
  activeModels: number
  uptime: number // seconds
}

export interface Dataset {
  name: string
  imageCount: number
  description: string
  lastUpdated: string // ISO date string
  classDistribution: { name: string; value: number }[]
}

export type DatasetStats = Dataset[]

export interface TestHistoryItem {
  id: string
  testTime: string // ISO date string
  models: string[]
  dataset: string
  results: {
    fps: number
    accuracy: number
  }
}

export type TestHistory = TestHistoryItem[]
