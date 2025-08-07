#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具包
"""

from src.website_builder.simple_intent_website_builder import SimpleIntentWebsiteBuilder
from src.website_builder.builder_core import IntentBasedWebsiteBuilder
from src.website_builder.structure_generator import WebsiteStructureGenerator
from src.website_builder.content_planner import ContentPlanGenerator
from src.website_builder.page_templates import PageTemplateManager
from src.website_builder.utils import (
    ensure_dir, load_data_file, save_json_file, 
    get_intent_description, generate_url_slug, 
    format_date, truncate_text, count_words
)

__all__ = [
    'SimpleIntentWebsiteBuilder',
    'IntentBasedWebsiteBuilder',
    'WebsiteStructureGenerator',
    'ContentPlanGenerator',
    'PageTemplateManager',
    'ensure_dir',
    'load_data_file',
    'save_json_file',
    'get_intent_description',
    'generate_url_slug',
    'format_date',
    'truncate_text',
    'count_words'
]
