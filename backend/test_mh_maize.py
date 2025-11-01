import requests
import json

response = requests.post(
    "http://localhost:8000/ask",
    json={"question": "Compare the average annual rainfall in Karnataka and Maharashtra for the last 5 years. List the top 3 most produced crops of Maize in each of those states during the same period."}
)

data = response.json()
print("\n✅ API Response received!\n")

# Find the crops table
for table in data['tables']:
    if 'Top' in table['title']:
        print(f"📊 {table['title']}")
        print(f"   Headers: {table['headers']}")
        print("\n   Data:")
        for row in table['rows']:
            print(f"   • {row[0]}: {row[1]} - {row[2]} tonnes")

print(f"\n✓ Answer: {data['answer'][:100]}...")
