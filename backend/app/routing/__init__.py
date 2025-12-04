#!/usr/bin/env python3
"""
Routing Module for AI Workload Distribution
Provides LISP and DNS-based routing implementations.
"""

from .lisp_router import LISPRouter
from .dns_router import DNSRouter

__all__ = ["LISPRouter", "DNSRouter"]