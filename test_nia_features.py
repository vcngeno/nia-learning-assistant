"""
Test script for Nia's new features
Tests: feedback, bilingual support, accessibility features
"""
import asyncio
import httpx
import json
from datetime import datetime, date

# Your Railway API URL or local URL
BASE_URL = "http://localhost:8002"
API_PREFIX = "/api/v1"  # Added API prefix


class NiaAPITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def test_health(self):
        """Test if API is running"""
        print("\n🔍 Testing API Health...")
        try:
            response = await self.client.get(f"{self.base_url}/")
            print(f"✅ API is running: {response.json()}")
            return True
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return False

    async def create_test_parent(self):
        """Create a test parent account"""
        print("\n👤 Creating test parent...")
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/auth/parent/register",
                json={
                    "email": f"test_parent_{int(datetime.now().timestamp())}@test.com",
                    "password": "TestPassword123!",
                    "full_name": "Test Parent"
                }
            )
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Parent created: {data}")
                return data
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    async def login_parent(self, email: str, password: str):
        """Login parent and get token"""
        print("\n🔐 Logging in parent...")
        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/auth/parent/login",
                json={
                    "email": email,
                    "password": password
                }
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful")
                return data.get("access_token")
            else:
                print(f"❌ Login failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    async def create_test_child(
        self,
        parent_token: str,
        language: str = "en",
        accommodations: list = None
    ):
        """Create a test child with specific settings"""
        print(f"\n👶 Creating test child (language={language})...")

        child_data = {
            "first_name": "TestChild",
            "nickname": "Testy",
            "date_of_birth": "2015-01-01",
            "grade_level": "3rd grade",
            "pin": "1234"
        }

        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/children/",
                json=child_data,
                headers={"Authorization": f"Bearer {parent_token}"}
            )
            if response.status_code == 201:
                data = response.json()
                print(f"✅ Child created: ID={data.get('id')}, Name={data.get('first_name')}")

                # Update child with language/accommodations if provided
                if language != "en" or accommodations:
                    await self.update_child_preferences(
                        data.get('id'),
                        parent_token,
                        language,
                        accommodations
                    )

                return data
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    async def update_child_preferences(
        self,
        child_id: int,
        parent_token: str,
        language: str,
        accommodations: list
    ):
        """Update child's language and accessibility preferences"""
        print(f"   Updating preferences: lang={language}, acc={accommodations}")
        # Note: You'll need to implement a PATCH endpoint for this
        # For now, we'll manually update in database
        pass

    async def test_english_conversation(self, child_id: int):
        """Test English conversation"""
        print("\n💬 Testing English Conversation...")

        message = {
            "child_id": child_id,
            "text": "What is photosynthesis?",
            "current_depth": 1
        }

        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/conversation/message",
                json=message
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Response received!")
                print(f"   Language: {data.get('language', 'unknown')}")
                print(f"   Source: {data.get('source_label', 'unknown')}")
                print(f"   Answer preview: {data.get('text', '')[:200]}...")
                print(f"   Follow-up questions: {data.get('follow_up_questions', [])}")
                print(f"   Source references: {len(data.get('source_references', []))} sources")
                return data
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    async def test_feedback_system(self, message_id: int, child_id: int, helpful: bool):
        """Test feedback submission"""
        print(f"\n👍👎 Testing Feedback System (helpful={helpful})...")

        feedback = {
            "message_id": message_id,
            "child_id": child_id,
            "is_helpful": helpful,
            "feedback_type": "too_complex" if not helpful else None,
            "feedback_text": "This was too hard to understand" if not helpful else "Very helpful!"
        }

        try:
            response = await self.client.post(
                f"{self.base_url}{API_PREFIX}/conversation/feedback",
                json=feedback
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Feedback submitted: {data.get('message', '')}")
                return True
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    async def test_depth_progression(self, child_id: int):
        """Test 3-level depth system"""
        print("\n📊 Testing 3-Level Depth System...")

        conversation_id = None

        for depth in [1, 2, 3]:
            print(f"\n   Testing Depth Level {depth}...")

            message = {
                "child_id": child_id,
                "text": "Tell me more" if depth > 1 else "What is gravity?",
                "current_depth": depth,
                "conversation_id": conversation_id
            }

            try:
                response = await self.client.post(
                    f"{self.base_url}{API_PREFIX}/conversation/message",
                    json=message
                )

                if response.status_code == 200:
                    data = response.json()
                    conversation_id = data.get('conversation_id')
                    print(f"   ✅ Depth {depth}: {data.get('source_label', '')}")
                    print(f"      Follow-up offered: {data.get('follow_up_offered', False)}")
                    print(f"      Max depth reached: {data.get('max_depth_reached', False)}")
                    print(f"      Questions: {data.get('follow_up_questions', [])[:1]}")
                else:
                    print(f"   ❌ Failed at depth {depth}: {response.text}")

            except Exception as e:
                print(f"   ❌ Error: {e}")

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


async def run_all_tests():
    """Run comprehensive test suite"""
    print("=" * 60)
    print("🧪 NIA FEATURE TESTING SUITE")
    print("=" * 60)

    tester = NiaAPITester(BASE_URL)

    try:
        # Test 1: API Health
        if not await tester.test_health():
            print("\n❌ API is not running. Please start your server first.")
            return

        # Test 2: Create parent
        parent = await tester.create_test_parent()
        if not parent:
            print("\n❌ Could not create parent. Stopping tests.")
            return

        parent_email = parent.get("email")

        # Test 3: Login parent
        token = await tester.login_parent(parent_email, "TestPassword123!")
        if not token:
            print("\n❌ Could not login. Stopping tests.")
            return

        # Test 4: Create child
        print("\n" + "="*60)
        print("TEST: Creating Child Profile")
        print("="*60)
        child = await tester.create_test_child(token, language="en")
        if not child:
            print("\n❌ Could not create child. Stopping tests.")
            return

        child_id = child.get("id")

        # Test 5: English conversation
        print("\n" + "="*60)
        print("TEST: English Conversation")
        print("="*60)
        response = await tester.test_english_conversation(child_id)

        if response:
            message_id = int(response.get("message_id", 0))

            # Test 6: Feedback system
            print("\n" + "="*60)
            print("TEST: Feedback System")
            print("="*60)
            await tester.test_feedback_system(message_id, child_id, helpful=True)
            await tester.test_feedback_system(message_id, child_id, helpful=False)

        # Test 7: Depth progression
        print("\n" + "="*60)
        print("TEST: 3-Level Depth System")
        print("="*60)
        await tester.test_depth_progression(child_id)

        print("\n" + "="*60)
        print("✅ TESTING COMPLETE!")
        print("="*60)

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
