#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具命令行入口
"""

import sys
from src.website_builder.cli import main

if __name__ == "__main__":
    sys.exit(main())