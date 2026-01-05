#!/bin/bash

# Test website generation

echo "🧪 Testing AI Website Builder..."
echo ""

echo "Testing with username: 'testuser'"
echo "This will use mock data since Topmate API is unavailable"
echo ""
echo "⏱️  This will take 30-60 seconds..."
echo ""

curl -X POST http://localhost:8001/api/build/website \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","user_prompt":"Create a modern portfolio website"}' \
  --output /tmp/generated-website.json

echo ""
echo ""

if [ -f /tmp/generated-website.json ]; then
    if grep -q "success.*true" /tmp/generated-website.json; then
        echo "✅ Website generation successful!"
        echo ""

        # Extract HTML and save to file
        python3 -c "
import json
with open('/tmp/generated-website.json') as f:
    data = json.load(f)
    if 'html' in data:
        with open('/tmp/generated-website.html', 'w') as out:
            out.write(data['html'])
        print('📄 HTML saved to: /tmp/generated-website.html')
        print('📊 Model used:', data.get('model', 'unknown'))
        print('⏱️  Generation time:', f\"{data.get('execution_time', 0):.2f}s\")
        print('')
        print('🌐 Open the HTML file to see the generated website!')
    else:
        print('❌ No HTML in response')
" || echo "Note: Install python3 to extract HTML"
    else
        echo "❌ Generation failed. Check the response:"
        cat /tmp/generated-website.json | head -200
    fi
else
    echo "❌ No response file created"
fi
