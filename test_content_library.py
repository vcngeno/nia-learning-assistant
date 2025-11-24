"""
Test Educational Content Library Integration
"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "https://web-production-5e612.up.railway.app"
API_PREFIX = "/api/v1"


class ContentLibraryTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.parent_token = None
        self.child_id = None

    async def setup_test_user(self):
        """Create test parent and child"""
        print("\n👤 Setting up test user...")

        # Register parent
        email = f"content_test_{int(datetime.now().timestamp())}@test.com"
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/auth/parent/register",
            json={
                "email": email,
                "password": "TestPass123!",
                "full_name": "Content Test Parent"
            }
        )

        # Login
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/auth/parent/login",
            json={"email": email, "password": "TestPass123!"}
        )
        self.parent_token = response.json().get("access_token")

        # Create child
        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/children/",
            json={
                "first_name": "ContentTestChild",
                "nickname": "CTC",
                "date_of_birth": "2015-05-15",
                "grade_level": "3rd grade",
                "pin": "1234"
            },
            headers={"Authorization": f"Bearer {self.parent_token}"}
        )
        self.child_id = response.json().get("id")
        print(f"✅ Test user created: Child ID {self.child_id}")

    async def test_math_question_with_content(self):
        """Test math question that should use curated content"""
        print("\n🔢 Testing Math Question (Fractions)...")

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json={
                "child_id": self.child_id,
                "text": "How do I add fractions with the same denominator?",
                "current_depth": 1
            }
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Source: {data.get('source_label')}")
        print(f"   Has curated content: {data.get('has_curated_content')}")
        print(f"   Number of sources: {len(data.get('sources', []))}")
        print(f"   Answer preview: {data.get('text')[:200]}...")

        if data.get('sources'):
            print(f"\n   📚 Sources used:")
            for source in data['sources']:
                print(f"      - {source['title']} ({source['type']})")

        # Check folder
        conv_id = data.get('conversation_id')
        conv_response = await self.client.get(
            f"{self.base_url}{API_PREFIX}/conversation/conversations/{self.child_id}"
        )
        conversations = conv_response.json().get('conversations', [])
        if conversations:
            folder = conversations[0].get('folder')
            print(f"   📁 Auto-categorized to folder: {folder}")

        return data

    async def test_science_question_with_content(self):
        """Test science question that should use curated content"""
        print("\n🔬 Testing Science Question (Photosynthesis)...")

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json={
                "child_id": self.child_id,
                "text": "What is photosynthesis and how does it work?",
                "current_depth": 1
            }
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Source: {data.get('source_label')}")
        print(f"   Has curated content: {data.get('has_curated_content')}")
        print(f"   Number of sources: {len(data.get('sources', []))}")

        if data.get('sources'):
            for source in data['sources']:
                print(f"   📚 Source: {source['title']} - {source['subject']}")

    async def test_geography_question(self):
        """Test geography question"""
        print("\n🌎 Testing Geography Question (US States)...")

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json={
                "child_id": self.child_id,
                "text": "What are the 5 regions of the United States?",
                "current_depth": 1
            }
        )

        if response.status_code != 200:
            print(f"❌ Failed: {response.status_code}")
            return

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Has curated content: {data.get('has_curated_content')}")
        print(f"   Sources: {len(data.get('sources', []))}")

    async def test_folder_organization(self):
        """Test that conversations are organized into folders"""
        print("\n📁 Testing Folder Organization...")

        # Get all folders
        response = await self.client.get(
            f"{self.base_url}{API_PREFIX}/conversation/folders/{self.child_id}"
        )

        folders = response.json().get('folders', [])
        print(f"✅ Folders created: {folders}")

        # Get conversations by folder
        for folder in folders:
            response = await self.client.get(
                f"{self.base_url}{API_PREFIX}/conversation/conversations/{self.child_id}?folder={folder}"
            )
            convs = response.json().get('conversations', [])
            print(f"   📂 {folder}: {len(convs)} conversation(s)")
            for conv in convs:
                print(f"      - {conv['title']}")

    async def test_general_knowledge_fallback(self):
        """Test question without curated content (should use general knowledge)"""
        print("\n🌐 Testing General Knowledge Fallback...")

        response = await self.client.post(
            f"{self.base_url}{API_PREFIX}/conversation/message",
            json={
                "child_id": self.child_id,
                "text": "What is a black hole?",
                "current_depth": 1
            }
        )

        data = response.json()
        print(f"✅ Response received!")
        print(f"   Source: {data.get('source_label')}")
        print(f"   Has curated content: {data.get('has_curated_content')}")
        print(f"   (Should be False - no astronomy content yet)")

    async def close(self):
        await self.client.aclose()


async def run_content_library_tests():
    """Run all content library tests"""
    print("=" * 60)
    print("📚 TESTING EDUCATIONAL CONTENT LIBRARY")
    print("=" * 60)

    tester = ContentLibraryTester(BASE_URL)

    try:
        await tester.setup_test_user()
        await tester.test_math_question_with_content()
        await tester.test_science_question_with_content()
        await tester.test_geography_question()
        await tester.test_folder_organization()
        await tester.test_general_knowledge_fallback()

        print("\n" + "=" * 60)
        print("✅ CONTENT LIBRARY TESTING COMPLETE!")
        print("=" * 60)

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(run_content_library_tests())
