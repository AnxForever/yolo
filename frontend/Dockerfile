# 1. 基镜像：选择一个包含Node.js LTS版本的镜像
FROM node:18-alpine AS base

# 2. 设置工作目录
WORKDIR /app

# 3. 复制依赖管理文件
COPY package.json pnpm-lock.yaml* ./

# 4. 安装pnpm并安装依赖
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# 5. 复制项目代码
COPY . .

# 6. 构建应用
RUN pnpm build

# 7. 创建生产环境镜像
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# 8. 复制构建产物和必要文件
COPY --from=base /app/public ./public
COPY --from=base /app/.next ./.next
COPY --from=base /app/node_modules ./node_modules
COPY --from=base /app/package.json ./package.json

# 9. 暴露端口
EXPOSE 3000

# 10. 启动命令
CMD ["pnpm", "start"] 