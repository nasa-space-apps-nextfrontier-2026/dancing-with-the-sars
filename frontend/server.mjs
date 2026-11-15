import { createServer } from 'node:http'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { extname, resolve, sep } from 'node:path'

const root = fileURLToPath(new URL('./dist/', import.meta.url))
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.ico': 'image/x-icon', '.txt': 'text/plain; charset=utf-8', '.woff2': 'font/woff2' }

const server = createServer(async (req, res) => {
  res.setHeader('X-Content-Type-Options', 'nosniff')
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin')
  if (!['GET', 'HEAD'].includes(req.method)) {
    res.writeHead(405, { Allow: 'GET, HEAD' }).end()
    return
  }
  let path
  try { path = decodeURIComponent(new URL(req.url, 'http://localhost').pathname) } catch {
    res.writeHead(400).end()
    return
  }
  // Only the two public React routes receive the SPA entry page.
  if (path === '/' || path === '/map' || path === '/map/') path = '/index.html'
  const file = resolve(root, `.${path}`)
  if (!file.startsWith(resolve(root) + sep) || path.split('/').some(p => p.startsWith('.')) || path.includes('\\')) {
    res.writeHead(404).end()
    return
  }
  try {
    const body = await readFile(file)
    res.writeHead(200, {
      'Content-Type': types[extname(file)] || 'application/octet-stream',
      'Content-Length': body.length,
      'Cache-Control': path.startsWith('/assets/') ? 'public, max-age=31536000, immutable' : 'no-cache',
    })
    res.end(req.method === 'HEAD' ? undefined : body)
  } catch (error) {
    res.writeHead(['ENOENT', 'EISDIR', 'ENOTDIR'].includes(error.code) ? 404 : 500).end()
  }
})

server.listen(Number(process.env.PORT || 8080), '0.0.0.0', () => console.log('RescueForce public demo listening'))
