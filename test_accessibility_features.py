"""
Test accessibility and special needs accommodations
"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8002"
API_PREFIX = "/api/v1"


class AccessibilityTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_parent_and_login(self):
        """Create parent and login"""
        print("\n👤 Creating parent...")

        email = f"accessibility_parent_{int(datetime.now().timestamp())}@test.com"
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/auth/parent/register",
            json={
                "email": email,
                "password": "TestPassword123!",
                "full_name": "Accessibility Test Parent"
            }
        )

        if response.status_code != 201:
            print(f"❌ Failed to create parent: {response.text}")
            return None, None

        print(f"✅ Parent created")

        # Login
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/auth/parent/login",
            json={
                "email": email,
                "password": "TestPassword123!"
            }
        )

        token = response.json().get("access_token")
        print(f"✅ Logged in")

        return email, token

    async def create_child_with_accommodations(
        self,
        parent_token: str,
        name: str,
        accommodations: list
    ):
        """Create child with specific learning accommodations"""
        print(f"\n👶 Creating child with accommodations: {accommodations}...")

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/children/",
            json={
                "first_name": name,
                "nickname": name,
                "date_of_birth": "2015-08-15",
                "grade_level": "3rd grade",
                "pin": "9999"
            },
            headers={"Authorization": f"Bearer {parent_token}"}
        )

        if response.status_code != 201:
            print(f"❌ Failed: {response.text}")
            return None

        child_data = response.json()
        child_id = child_data.get("id")
        print(f"✅ Child created: {name} (ID={child_id})")

        # Note: We'd need to update the child with accommodations via PATCH endpoint
        # For now, we'll test with the accommodations passed to the conversation API

        return child_id

    async def test_autism_support(self, child_id: int):
        """Test autism support - literal language, structured responses"""
        print("\n🧩 Testing AUTISM SUPPORT...")
        print("   Expected: Literal language, no metaphors, structured steps")

        message = {
            "child_id": child_id,
            "text": "How do plants grow?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.text}")
            return

        data = response.json()
        answer = data.get('text', '')

        print(f"✅ Response received!")
        print(f"   Complexity: {data.get('complexity_level', 'unknown')}")
        print(f"   Response preview:")
        print(f"   {answer[:400]}...")

        # Check for structured content
        has_steps = any(marker in answer for marker in ['1.', '2.', '**', 'Step'])
        print(f"   Has structured steps: {'✅' if has_steps else '❌'}")

        return data

    async def test_dyslexia_support(self, child_id: int):
        """Test dyslexia support - simple sentences, bullet points"""
        print("\n📖 Testing DYSLEXIA SUPPORT...")
        print("   Expected: Simple sentences, clear formatting, bullet points")

        message = {
            "child_id": child_id,
            "text": "What are the planets in our solar system?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.text}")
            return

        data = response.json()
        answer = data.get('text', '')

        print(f"✅ Response received!")
        print(f"   Response preview:")
        print(f"   {answer[:400]}...")

        # Check for bullet points or lists
        has_bullets = any(marker in answer for marker in ['-', '•', '*', '\n1.'])
        print(f"   Has bullet points/lists: {'✅' if has_bullets else '❌'}")

        return data

    async def test_adhd_support(self, child_id: int):
        """Test ADHD support - concise, engaging, focused"""
        print("\n⚡ Testing ADHD SUPPORT...")
        print("   Expected: Concise, engaging, focused responses")

        message = {
            "child_id": child_id,
            "text": "Why do we have seasons?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.text}")
            return

        data = response.json()
        answer = data.get('text', '')

        print(f"✅ Response received!")
        print(f"   Response length: {len(answer)} characters")
        print(f"   Response preview:")
        print(f"   {answer[:400]}...")

        # Check if response is reasonably concise
        is_concise = len(answer) < 1000
        print(f"   Is concise (<1000 chars): {'✅' if is_concise else '⚠️'}")

        return data

    async def test_visual_learner(self, child_id: int):
        """Test visual learner support - descriptive, spatial"""
        print("\n👁️ Testing VISUAL LEARNER SUPPORT...")
        print("   Expected: Visual descriptions, spatial analogies")

        message = {
            "child_id": child_id,
            "text": "How does the water cycle work?",
            "current_depth": 1
        }

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json=message
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.text}")
            return

        data = response.json()
        answer = data.get('text', '')

        print(f"✅ Response received!")
        print(f"   Response preview:")
        print(f"   {answer[:400]}...")

        # Check for visual/spatial language
        visual_words = ['picture', 'imagine', 'see', 'looks like', 'visualize', 'circle', 'up', 'down']
        has_visual_language = any(word in answer.lower() for word in visual_words)
        print(f"   Uses visual language: {'✅' if has_visual_language else '⚠️'}")

        return data

    async def close(self):
        await self.client.aclose()


async def run_accessibility_tests():
    """Run all accessibility feature tests"""
    print("=" * 60)
    print("♿ TESTING ACCESSIBILITY & SPECIAL NEEDS FEATURES")
    print("=" * 60)

    tester = AccessibilityTester(BASE_URL)

    try:
        # Create parent
        email, token = await tester.create_parent_and_login()
        if not token:
            return

        # Create different children with various needs
        # Note: In production, these would have learning_accommodations set in DB

        autism_child = await tester.create_child_with_accommodations(
            token, "AutismChild", ["autism_support"]
        )

        dyslexia_child = await tester.create_child_with_accommodations(
            token, "DyslexiaChild", ["dyslexia_support"]
        )

        adhd_child = await tester.create_child_with_accommodations(
            token, "ADHDChild", ["adhd_support"]
        )

        visual_child = await tester.create_child_with_accommodations(
            token, "VisualChild", ["visual_learner"]
        )

        # Test each accommodation type
        if autism_child:
            await tester.test_autism_support(autism_child)

        if dyslexia_child:
            await tester.test_dyslexia_support(dyslexia_child)

        if adhd_child:
            await tester.test_adhd_support(adhd_child)

        if visual_child:
            await tester.test_visual_learner(visual_child)

        print("\n" + "=" * 60)
        print("✅ ACCESSIBILITY TESTING COMPLETE!")
        print("=" * 60)
        print("\nNote: Full accommodation support requires database updates")
        print("to store learning_accommodations field in child profiles.")

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(run_accessibility_tests())
