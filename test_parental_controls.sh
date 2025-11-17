#!/bin/bash

API_URL="https://web-production-a4ec.up.railway.app"

echo "🧪 Testing Parental Controls..."
echo

# 1. Register Parent
echo "1️⃣ Registering parent..."
PARENT_RESPONSE=$(curl -s -X POST $API_URL/parents/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test'$(date +%s)'@example.com",
    "name": "Test Parent",
    "phone": "+1234567890",
    "pin": "1234"
  }')

echo $PARENT_RESPONSE | jq '.'
TOKEN=$(echo $PARENT_RESPONSE | jq -r '.access_token')
PARENT_ID=$(echo $PARENT_RESPONSE | jq -r '.parent_id')
echo

# 2. Create Student
echo "2️⃣ Creating student..."
STUDENT_RESPONSE=$(curl -s -X POST $API_URL/parents/students/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "parent_id": "'$PARENT_ID'",
    "name": "TestKid",
    "age": 10,
    "grade": 5
  }')

echo $STUDENT_RESPONSE | jq '.'
STUDENT_ID=$(echo $STUDENT_RESPONSE | jq -r '.student_id')
echo

# 3. Send a chat message
echo "3️⃣ Sending chat message..."
CHAT_RESPONSE=$(curl -s -X POST $API_URL/chat \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "'$STUDENT_ID'",
    "message": "What is photosynthesis?"
  }')

echo $CHAT_RESPONSE | jq '.'
echo

# 4. Check dashboard
echo "4️⃣ Checking parent dashboard..."
curl -s $API_URL/parents/dashboard/$STUDENT_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo

# 5. Check session status
echo "5️⃣ Checking session status..."
curl -s $API_URL/session/check/$STUDENT_ID | jq '.'
echo

echo "✅ All tests completed!"
echo "Parent ID: $PARENT_ID"
echo "Student ID: $STUDENT_ID"
echo "Access Token: $TOKEN"
