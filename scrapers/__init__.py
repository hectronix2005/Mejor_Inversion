"""
Sistema de Scraping de CDTs - Colombia
"""
from .base_scraper import BaseScraper
from .config import BANKS_CONFIG, STANDARD_TERMS, STANDARD_AMOUNTS

__all__ = ['BaseScraper', 'BANKS_CONFIG', 'STANDARD_TERMS', 'STANDARD_AMOUNTS']
