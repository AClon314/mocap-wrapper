import { defineConfig } from "astro/config";
import { type ViteDevServer } from "vite";
import vue from "@astrojs/vue";
import tailwindcss from "@tailwindcss/vite";

const ASSET_PREFIX = "/proxy/4321";
const MODE = import.meta.env.MODE;
const isDev = MODE === "development";

// 从环境变量读取 allowedHosts，多个主机用逗号分隔
const ALLOWED_HOSTS = import.meta.env.VITE_ALLOWED_HOSTS
  ? import.meta.env.VITE_ALLOWED_HOSTS.split(",").map((h: string) => h.trim())
  : [];

// https://astro.build/config
export default defineConfig({
  // https://docs.astro.build/en/guides/integrations-guide/vue/#appentrypoint
  integrations: [vue({ appEntrypoint: "/src/main" })],

  vite: {
    plugins: [
      tailwindcss(),
      // 仅在开发模式添加该插件
      // ...(isDev ? [devAssetPrefixPlugin()] : []),
    ],
    // Ensure the runtime compiler build of Vue is used so components that
    // provide a `template` option (like the inline SVG icon objects) work.
    resolve: {
      alias: {
        vue: "vue/dist/vue.esm-bundler.js",
      },
    },
    server: {
      strictPort: true, // 如果端口被占用就报错，避免动态分配
      allowedHosts: ALLOWED_HOSTS,
    },
  },
});

// 仅在开发模式下使用的插件
function devAssetPrefixPlugin() {
  return {
    name: "dev-asset-prefix",
    configureServer(server: ViteDevServer) {
      // 1. 请求路径重写：/proxy/4321/xxx → /xxx
      // server.middlewares.use((req, _, next) => {
      //   console.debug("devAssetPrefixPlugin", req.url);
      //   if (req.url?.startsWith(ASSET_PREFIX + "/")) {
      //     req.originalUrl = req.url;
      //     req.url = req.url.slice(ASSET_PREFIX.length);
      //   }
      //   next();
      // });

      // FIXME: HTML 响应重写：给资源路径加前缀
      server.middlewares.use((req, res, next) => {
        if (!req.headers.accept?.includes("text/html")) {
          return next();
        }

        const originalEnd = res.end;
        let body = "";

        res.end = function (chunk) {
          body += chunk || "";
          // 只替换以 "/" 开头且不包含 ASSET_PREFIX 的资源
          body = body.replace(
            /(src|href)="\/(?!proxy\/4321)([^"]+)"/g,
            `$1="${ASSET_PREFIX}/$2"`
          );
          originalEnd.call(this, body);
        };

        next();
      });
    },
  };
}
