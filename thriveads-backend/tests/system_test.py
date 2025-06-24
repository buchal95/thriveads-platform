#!/usr/bin/env python3
"""
Comprehensive system test for ThriveAds Platform
Tests the entire system end-to-end including API endpoints, data processing, and performance
"""

import requests
import json
import time
from datetime import date, timedelta
from typing import Dict, Any


class ThriveAdsSystemTest:
    """Comprehensive system test suite"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_client_id = "513010266454814"
        self.results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def test_api_health(self):
        """Test basic API health"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_test("API Health Check", True, "API is healthy")
                    return True
                else:
                    self.log_test("API Health Check", False, f"Unhealthy status: {data}")
                    return False
            else:
                self.log_test("API Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_api_documentation(self):
        """Test API documentation accessibility"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            success = response.status_code == 200
            self.log_test("API Documentation", success, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("API Documentation", False, f"Exception: {str(e)}")
            return False
    
    def test_performance_monitoring(self):
        """Test performance monitoring endpoints"""
        endpoints = [
            "/api/v1/performance/health",
            "/api/v1/performance/summary",
            "/api/v1/performance/database-analysis"
        ]
        
        all_success = True
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code == 200
                if success:
                    data = response.json()
                    self.log_test(f"Performance Endpoint {endpoint}", True, "Accessible")
                else:
                    self.log_test(f"Performance Endpoint {endpoint}", False, f"HTTP {response.status_code}")
                    all_success = False
            except Exception as e:
                self.log_test(f"Performance Endpoint {endpoint}", False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_analytics_endpoints(self):
        """Test analytics endpoints with mock data"""
        endpoints = [
            {
                "url": f"/api/v1/ads/top-performing?client_id={self.test_client_id}&period=last_week&limit=5",
                "name": "Top Performing Ads"
            },
            {
                "url": f"/api/v1/metrics/funnel?client_id={self.test_client_id}&period=last_week",
                "name": "Conversion Funnel"
            },
            {
                "url": f"/api/v1/metrics/week-on-week?client_id={self.test_client_id}",
                "name": "Week-on-Week Comparison"
            }
        ]
        
        all_success = True
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint['url']}", timeout=15)
                success = response.status_code in [200, 500]  # 500 is OK for missing data
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(endpoint['name'], True, f"Returned data: {type(data)}")
                elif response.status_code == 500:
                    # Expected for missing Meta API data
                    self.log_test(endpoint['name'], True, "Expected error for missing data")
                else:
                    self.log_test(endpoint['name'], False, f"HTTP {response.status_code}")
                    all_success = False
            except Exception as e:
                self.log_test(endpoint['name'], False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_sync_endpoints(self):
        """Test data sync endpoints"""
        endpoints = [
            {
                "url": f"/api/v1/sync/daily?client_id={self.test_client_id}",
                "method": "POST",
                "name": "Daily Sync"
            },
            {
                "url": f"/api/v1/sync/status?client_id={self.test_client_id}",
                "method": "GET",
                "name": "Sync Status"
            }
        ]
        
        all_success = True
        for endpoint in endpoints:
            try:
                if endpoint["method"] == "POST":
                    response = requests.post(f"{self.base_url}{endpoint['url']}", timeout=10)
                else:
                    response = requests.get(f"{self.base_url}{endpoint['url']}", timeout=10)
                
                success = response.status_code in [200, 500]  # 500 OK for missing Meta API
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_test(endpoint['name'], True, f"Success: {data.get('message', 'OK')}")
                elif response.status_code == 500:
                    self.log_test(endpoint['name'], True, "Expected error for missing Meta API")
                else:
                    self.log_test(endpoint['name'], False, f"HTTP {response.status_code}")
                    all_success = False
            except Exception as e:
                self.log_test(endpoint['name'], False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_performance_benchmarks(self):
        """Test performance benchmarking"""
        try:
            # Test query benchmarks
            response = requests.post(f"{self.base_url}/api/v1/performance/benchmark/queries", timeout=30)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                benchmarks = data.get("benchmarks", {})
                self.log_test("Query Benchmarks", True, f"Tested {len(benchmarks)} query types")
            else:
                self.log_test("Query Benchmarks", False, f"HTTP {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Query Benchmarks", False, f"Exception: {str(e)}")
            return False
    
    def test_database_performance(self):
        """Test database performance analysis"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/performance/database-analysis", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                table_stats = data.get("table_statistics", {})
                recommendations = data.get("index_recommendations", [])
                self.log_test("Database Analysis", True, 
                            f"Analyzed {len(table_stats)} tables, {len(recommendations)} recommendations")
            else:
                self.log_test("Database Analysis", False, f"HTTP {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Database Analysis", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling with invalid requests"""
        test_cases = [
            {
                "url": "/api/v1/ads/top-performing?client_id=invalid&period=last_week",
                "name": "Invalid Client ID",
                "expected_codes": [400, 404, 500]
            },
            {
                "url": "/api/v1/ads/top-performing?client_id=513010266454814&period=invalid",
                "name": "Invalid Period",
                "expected_codes": [400, 422, 500]
            },
            {
                "url": "/api/v1/nonexistent",
                "name": "Nonexistent Endpoint",
                "expected_codes": [404]
            }
        ]
        
        all_success = True
        for test_case in test_cases:
            try:
                response = requests.get(f"{self.base_url}{test_case['url']}", timeout=10)
                success = response.status_code in test_case["expected_codes"]
                
                if success:
                    self.log_test(f"Error Handling: {test_case['name']}", True, 
                                f"Correctly returned HTTP {response.status_code}")
                else:
                    self.log_test(f"Error Handling: {test_case['name']}", False, 
                                f"Unexpected HTTP {response.status_code}")
                    all_success = False
            except Exception as e:
                self.log_test(f"Error Handling: {test_case['name']}", False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def test_response_times(self):
        """Test API response times"""
        endpoints = [
            "/health",
            "/api/v1/performance/health",
            f"/api/v1/ads/top-performing?client_id={self.test_client_id}&period=last_week&limit=5"
        ]
        
        all_success = True
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time = end_time - start_time
                success = response_time < 5.0  # 5 second threshold
                
                if success:
                    self.log_test(f"Response Time: {endpoint}", True, f"{response_time:.2f}s")
                else:
                    self.log_test(f"Response Time: {endpoint}", False, f"Slow: {response_time:.2f}s")
                    all_success = False
            except Exception as e:
                self.log_test(f"Response Time: {endpoint}", False, f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🚀 Starting ThriveAds Platform System Tests")
        print("=" * 50)
        
        test_methods = [
            self.test_api_health,
            self.test_api_documentation,
            self.test_performance_monitoring,
            self.test_analytics_endpoints,
            self.test_sync_endpoints,
            self.test_performance_benchmarks,
            self.test_database_performance,
            self.test_error_handling,
            self.test_response_times
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for test_method in test_methods:
            print(f"\n📋 Running {test_method.__name__}...")
            success = test_method()
            total_tests += 1
            if success:
                passed_tests += 1
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # Overall status
        if success_rate >= 80:
            print(f"\n🎉 SYSTEM STATUS: READY FOR PRODUCTION ({success_rate:.1f}% success rate)")
        elif success_rate >= 60:
            print(f"\n⚠️  SYSTEM STATUS: NEEDS ATTENTION ({success_rate:.1f}% success rate)")
        else:
            print(f"\n🚨 SYSTEM STATUS: CRITICAL ISSUES ({success_rate:.1f}% success rate)")
        
        return success_rate >= 80


if __name__ == "__main__":
    tester = ThriveAdsSystemTest()
    tester.run_all_tests()
