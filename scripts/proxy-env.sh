#!/usr/bin/env bash
# 与 macOS 系统代理一致（scutil --proxy → 127.0.0.1:12334）
# 用法: source scripts/proxy-env.sh

export http_proxy="http://127.0.0.1:12334"
export https_proxy="http://127.0.0.1:12334"
export HTTP_PROXY="http://127.0.0.1:12334"
export HTTPS_PROXY="http://127.0.0.1:12334"
export ALL_PROXY="socks5://127.0.0.1:12334"

echo "Proxy enabled → 127.0.0.1:12334"
