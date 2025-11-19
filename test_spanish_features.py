"""
Test Spanish language features
"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8002"
API_PREFIX = "/api/v1"


class SpanishTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_parent_and_login(self):
        """Create parent and login"""
        print("\n👤 Creating Spanish-speaking parent...")

        # Register
        email = f"spanish_parent_{int(datetime.now().timestamp())}@test.com"
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/auth/parent/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "full_name": "Padre de Prueba"
            }
        )

        if response.status_code != 201:
            print(f"❌ Failed to create parent: {response.text}")
            return None, None

        print(f"✅ Parent created: {email}")

        # Login
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/auth/parent/login",
            json={
                "email": email,
                "password": "TestPassword123!"
            }
        )

        if response.status_code != 200:
            print(f"❌ Failed to login: {response.text}")
            return None, None

        token = response.json().get("access_token")
        print(f"✅ Logged in successfully")

        return email, token

    async def create_spanish_child(self, parent_token: str):
        """Create a child with Spanish language preference"""
        print("\n👶 Creating Spanish-speaking child...")

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/children/",
            json={
                "first_name": "Juanito",
                "nickname": "Juan",
                "date_of_birth": "2015-05-10",
                "grade_level": "3rd grade",
                "pin": "5678"
            },
            headers={"Authorization": f"Bearer {parent_token}"}
        )

        if response.status_code != 201:
            print(f"❌ Failed to create child: {response.text}")
            return None

        child_data = response.json()
        child_id = child_data.get("id")
        print(f"✅ Child created: ID={child_id}, Name={child_data.get('first_name')}")

        return child_id

    async def test_spanish_conversation_simple(self, child_id: int):
        """Test simple Spanish conversation"""
        print("\n💬 Testing Spanish Conversation (Simple Question)...")

        message = {
            "child_id": child_id,
            "text": "¿Qué es la fotosíntesis?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Language: {data.get('language', 'unknown')}")
        print(f"   Source: {data.get('source_label', 'unknown')}")
        print(f"   Answer preview: {data.get('text', '')[:300]}...")
        print(f"   Follow-up questions: {data.get('follow_up_questions', [])}")

        return data

    async def test_spanish_math_question(self, child_id: int):
        """Test Spanish math question"""
        print("\n🔢 Testing Spanish Math Question...")

        message = {
            "child_id": child_id,
            "text": "¿Cómo sumo fracciones?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Answer preview: {data.get('text', '')[:300]}...")
        print(f"   Depth level: {data.get('tutoring_depth_level')}")

        return data

    async def test_spanish_history_question(self, child_id: int):
        """Test Spanish history question"""
        print("\n📚 Testing Spanish History Question...")

        message = {
            "child_id": child_id,
            "text": "¿Quién fue George Washington?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Answer preview: {data.get('text', '')[:300]}...")

        return data

    async def test_mixed_language_handling(self, child_id: int):
        """Test what happens with English question from Spanish-speaking child"""
        print("\n🌐 Testing Mixed Language (English question)...")

        message = {
            "child_id": child_id,
            "text": "What is gravity?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return None

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Language detected: {data.get('language', 'unknown')}")
        print(f"   Answer preview: {data.get('text', '')[:200]}...")

        return data

    async def close(self):
        await self.client.aclose()


async def run_spanish_tests():
    """Run all Spanish feature tests"""
    print("=" * 60)
    print("🇪🇸 TESTING SPANISH LANGUAGE FEATURES")
    print("=" * 60)

    tester = SpanishTester(BASE_URL)

    try:
        # Create parent and login
        email, token = await tester.create_parent_and_login()
        if not token:
            print("\n❌ Cannot continue without parent authentication")
            return

        # Create Spanish-speaking child
        child_id = await tester.create_spanish_child(token)
        if not child_id:
            print("\n❌ Cannot continue without child profile")
            return

        # Test Spanish conversations
        await tester.test_spanish_conversation_simple(child_id)
        await tester.test_spanish_math_question(child_id)
        await tester.test_spanish_history_question(child_id)
        await tester.test_mixed_language_handling(child_id)

        print("\n" + "=" * 60)
        print("✅ SPANISH TESTING COMPLETE!")
        print("=" * 60)

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(run_spanish_tests())
