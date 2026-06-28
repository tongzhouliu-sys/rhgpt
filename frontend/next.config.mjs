/** @type {import('next').NextConfig} */
const nextConfig = {
  // All data flows are client-side fetches to the Railway backend, so the app
  // exports as a static bundle and deploys directly to Cloudflare Pages
  // (`next build` -> ./out). No server runtime / CF adapter needed for V1.
  output: "export",
  reactStrictMode: true,
  trailingSlash: true,
};

export default nextConfig;
