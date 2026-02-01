import { fileURLToPath, URL } from "node:url";

import { defineConfig, loadEnv } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";
import tailwindcss from '@tailwindcss/vite'

import fs from "fs";
import path from "path";
import { dirname } from "node:path";
import { execSync } from "child_process";
const __dirname = dirname(fileURLToPath(import.meta.url));
const vite_env = loadEnv("", __dirname);
const keyPath = path.resolve(__dirname, ".localhost.key");
const crtPath = path.resolve(__dirname, ".localhost.crt");
const isHttps = vite_env.VITE_HTTPS
function genCert() {
  if (!fs.existsSync(keyPath) || !fs.existsSync(crtPath)) {
    console.log("证书文件不存在，正在自动生成...");

    try {
      // 生成私钥
      execSync(`openssl genrsa -out ${keyPath} 2048`, { stdio: "inherit" });

      // 生成证书
      execSync(
        `openssl req -new -x509 -key ${keyPath} -out ${crtPath} -days 365 -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"`,
        { stdio: "inherit" },
      );

      console.log("SSL 证书已成功生成！");
    } catch (error) {
      console.error("生成 SSL 证书时出错:", error);
      throw error;
    }
  }
}

if (isHttps) genCert();

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueDevTools(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  assetsInclude: ['**/*.md'],
  server: {
    allowedHosts: [".ts.net"],
    host: true,
    https: isHttps ? {
      key: keyPath,
      cert: crtPath,
    } : undefined,
  },
});
