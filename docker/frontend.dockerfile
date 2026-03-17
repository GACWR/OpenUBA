FROM node:18-alpine AS base

# install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY interface/package.json interface/package-lock.json* ./
RUN npm install --legacy-peer-deps

# rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
# copy interface files (node_modules excluded via .dockerignore)
COPY interface/package.json interface/package-lock.json* ./

COPY interface/app ./app
COPY interface/src ./src
COPY interface/public ./public
COPY interface/next.config.js ./
COPY interface/next-env.d.ts ./
COPY interface/tailwind.config.js ./
COPY interface/postcss.config.js ./
COPY interface/tsconfig.json ./
COPY interface/components.json ./
# bake graphql URL as relative path so browser proxies through Next.js server
ENV NEXT_PUBLIC_GRAPHQL_URL=/graphql
RUN npm run build

# production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder /app/package.json ./package.json

USER nextjs

EXPOSE 3000

ENV PORT=3000

CMD ["node", "server.js"]

