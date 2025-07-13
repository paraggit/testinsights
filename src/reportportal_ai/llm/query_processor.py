# src/reportportal_ai/llm/query_processor.py
"""Natural language query processor."""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import structlog

from src.reportportal_ai.llm.providers.base import Message

logger = structlog.get_logger(__name__)


class QueryProcessor:
    """Processes natural language queries for ReportPortal data."""
    
    def __init__(self):
        # Common patterns for query understanding
        self.time_patterns = {
            r"last (\d+) (hour|day|week|month)s?": self._parse_relative_time,
            r"(today|yesterday)": self._parse_day_reference,
            r"this (week|month)": self._parse_current_period,
        }
        
        self.status_keywords = {
            "failed": ["FAILED"],
            "broken": ["BROKEN"],
            "passed": ["PASSED"],
            "skipped": ["SKIPPED"],
            "error": ["FAILED", "BROKEN"],
            "success": ["PASSED"],
        }
        
        self.entity_keywords = {
            "launch": ["launch", "run", "execution", "build"],
            "test": ["test", "case", "scenario", "spec"],
            "log": ["log", "error", "exception", "stacktrace"],
            "dashboard": ["dashboard", "widget", "chart"],
            "filter": ["filter", "saved search"],
        }
    
    def analyze_query(self, query: str) -> Dict[str, any]:
        """Analyze a natural language query and extract parameters."""
        query_lower = query.lower()
        
        analysis = {
            "original_query": query,
            "intent": self._detect_intent(query_lower),
            "entity_types": self._detect_entity_types(query_lower),
            "time_filter": self._extract_time_filter(query_lower),
            "status_filter": self._extract_status_filter(query_lower),
            "keywords": self._extract_keywords(query),
            "metrics_requested": self._detect_metrics_request(query_lower),
        }
        
        return analysis
    
    def _detect_intent(self, query: str) -> str:
        """Detect the primary intent of the query."""
        if any(word in query for word in ["how many", "count", "number of", "total"]):
            return "count"
        elif any(word in query for word in ["why", "root cause", "reason"]):
            return "analysis"
        elif any(word in query for word in ["trend", "over time", "history"]):
            return "trend"
        elif any(word in query for word in ["compare", "difference", "vs"]):
            return "comparison"
        elif any(word in query for word in ["show", "list", "find", "get"]):
            return "search"
        else:
            return "general"
    
    def _detect_entity_types(self, query: str) -> List[str]:
        """Detect which entity types are mentioned in the query."""
        detected = []
        
        for entity_type, keywords in self.entity_keywords.items():
            if any(keyword in query for keyword in keywords):
                if entity_type == "launch":
                    detected.append("launch")
                elif entity_type == "test":
                    detected.append("test_item")
                elif entity_type == "log":
                    detected.append("log")
                elif entity_type == "dashboard":
                    detected.append("dashboard")
                elif entity_type == "filter":
                    detected.append("filter")
        
        # Default to test items and launches if none detected
        if not detected:
            detected = ["launch", "test_item"]
        
        return detected
    
    def _extract_time_filter(self, query: str) -> Optional[Dict[str, any]]:
        """Extract time-based filters from the query."""
        for pattern, parser in self.time_patterns.items():
            match = re.search(pattern, query)
            if match:
                return parser(match)
        
        return None
    
    def _parse_relative_time(self, match) -> Dict[str, any]:
        """Parse relative time expressions like 'last 7 days'."""
        count = int(match.group(1))
        unit = match.group(2)
        
        now = datetime.utcnow()
        if unit == "hour":
            cutoff = now - timedelta(hours=count)
        elif unit == "day":
            cutoff = now - timedelta(days=count)
        elif unit == "week":
            cutoff = now - timedelta(weeks=count)
        elif unit == "month":
            cutoff = now - timedelta(days=count * 30)  # Approximate
        
        return {
            "start": cutoff,
            "end": now,
            "description": f"last {count} {unit}s"
        }
    
    def _parse_day_reference(self, match) -> Dict[str, any]:
        """Parse day references like 'today' or 'yesterday'."""
        reference = match.group(1)
        now = datetime.utcnow()
        
        if reference == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now
        else:  # yesterday
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return {
            "start": start,
            "end": end,
            "description": reference
        }
    
    def _parse_current_period(self, match) -> Dict[str, any]:
        """Parse current period references like 'this week'."""
        period = match.group(1)
        now = datetime.utcnow()
        
        if period == "week":
            # Start of week (Monday)
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # month
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return {
            "start": start,
            "end": now,
            "description": f"this {period}"
        }
    
    def _extract_status_filter(self, query: str) -> Optional[List[str]]:
        """Extract status filters from the query."""
        statuses = []
        
        for keyword, status_list in self.status_keywords.items():
            if keyword in query:
                statuses.extend(status_list)
        
        return list(set(statuses)) if statuses else None
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords for search."""
        # Remove common words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "shall", "can", "need", "show", "find",
            "get", "list", "what", "which", "when", "where", "who", "why", "how"
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _detect_metrics_request(self, query: str) -> bool:
        """Detect if the query is asking for metrics/statistics."""
        metrics_keywords = [
            "percentage", "rate", "ratio", "average", "mean", "median",
            "statistics", "stats", "metrics", "performance", "success rate",
            "failure rate", "pass rate", "distribution"
        ]
        
        return any(keyword in query for keyword in metrics_keywords)
    
    def build_search_query(self, analysis: Dict[str, any]) -> str:
        """Build an optimized search query from the analysis."""
        # Use keywords but prioritize error-related terms
        keywords = analysis["keywords"]
        
        # Add status-related terms if status filter is present
        if analysis["status_filter"]:
            for status in analysis["status_filter"]:
                keywords.append(status.lower())
        
        # Build search query
        search_query = " ".join(keywords)
        
        return search_query
    
    def build_system_prompt(self, analysis: Dict[str, any]) -> str:
        """Build a system prompt based on query analysis."""
        base_prompt = """You are an AI assistant specialized in analyzing ReportPortal test execution data. 
You help users understand test results, identify issues, and provide insights about test failures and trends.

When answering questions:
1. Be specific and reference actual data from the provided context
2. For test failures, identify patterns and common issues
3. Provide actionable insights when possible
4. Use clear formatting with bullet points for lists
5. If asked about metrics, calculate them from the provided data"""

        # Add intent-specific instructions
        if analysis["intent"] == "count":
            base_prompt += "\n\nFocus on providing accurate counts and statistics from the data."
        elif analysis["intent"] == "analysis":
            base_prompt += "\n\nFocus on analyzing root causes and patterns in test failures."
        elif analysis["intent"] == "trend":
            base_prompt += "\n\nFocus on identifying trends and changes over time."
        elif analysis["intent"] == "comparison":
            base_prompt += "\n\nFocus on comparing different aspects of the test data."
        
        return base_prompt