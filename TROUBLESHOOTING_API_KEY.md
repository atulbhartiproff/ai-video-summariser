# Troubleshooting: Gemini API Key "not valid" Error

## Quick Fix Steps

### Step 1: Verify the Secret Exists and Get Correct ARN

```bash
# Get the full ARN (includes random suffix like -a1b2c3)
SECRET_ARN=$(aws secretsmanager describe-secret \
  --secret-id ai-video-gemini-key \
  --region ap-southeast-2 \
  --query 'ARN' \
  --output text)

echo "Secret ARN: $SECRET_ARN"
```

### Step 2: Check How the Secret is Stored

```bash
# Get the secret value
aws secretsmanager get-secret-value \
  --secret-id ai-video-gemini-key \
  --region ap-southeast-2 \
  --query 'SecretString' \
  --output text
```

**Expected format:** Just the API key string: `AIzaSy...`  
**Wrong format:** JSON like `{"key": "AIzaSy..."}` or `{"GEMINI_API_KEY": "AIzaSy..."}`

### Step 3: Fix the Secret (if stored incorrectly)

If the secret is stored as JSON, update it to be a plain string:

```bash
# Replace YOUR_ACTUAL_API_KEY with your real Gemini API key
aws secretsmanager update-secret \
  --secret-id ai-video-gemini-key \
  --secret-string "YOUR_ACTUAL_API_KEY" \
  --region ap-southeast-2
```

**Important:** 
- The secret should be JUST the API key string
- No quotes, no JSON, no extra formatting
- Get your API key from: https://aistudio.google.com/app/apikey

### Step 4: Update Task Definition with Correct ARN

1. **Get the correct ARN:**
   ```bash
   aws secretsmanager describe-secret \
     --secret-id ai-video-gemini-key \
     --region ap-southeast-2 \
     --query 'ARN' \
     --output text
   ```

2. **Update your task definition JSON:**
   - Replace the `valueFrom` in the secrets section with the ARN from step 1
   - The ARN should look like: `arn:aws:secretsmanager:ap-southeast-2:899673281251:secret:ai-video-gemini-key-a1b2c3`
   - Note the `-a1b2c3` suffix (random characters) - this is required!

3. **Register the updated task definition:**
   ```bash
   aws ecs register-task-definition \
     --cli-input-json file://task-definition.json \
     --region ap-southeast-2
   ```

### Step 5: Verify ECS Task Execution Role Has Permissions

The ECS task execution role needs permission to read secrets:

```bash
# Check the task execution role
aws ecs describe-task-definition \
  --task-definition ai-video-summarizer \
  --region ap-southeast-2 \
  --query 'taskDefinition.executionRoleArn' \
  --output text
```

The role should have this policy attached:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:ap-southeast-2:899673281251:secret:ai-video-gemini-key-*"
    }
  ]
}
```

### Step 6: Check Backend Logs

After redeploying, check the backend container logs:

```bash
aws logs tail /ecs/ai-video-summarizer \
  --follow \
  --region ap-southeast-2 \
  --filter-pattern "backend"
```

Look for:
- `Gemini API Key loaded: AIzaSy... (length: XX)` - ✅ Good
- `GEMINI_API_KEY environment variable is required` - ❌ Secret not loaded
- No API key log message - ❌ Secret not loaded

### Step 7: Force New Deployment

After updating the task definition:

```bash
aws ecs update-service \
  --cluster ai-video-summarizer-cluster \
  --service ai-video-summarizer-service \
  --force-new-deployment \
  --region ap-southeast-2
```

## Common Mistakes

1. **Secret stored as JSON:**
   - ❌ Wrong: `{"GEMINI_API_KEY": "AIzaSy..."}`
   - ✅ Correct: `AIzaSy...`

2. **Wrong ARN in task definition:**
   - ❌ Wrong: `arn:aws:secretsmanager:ap-southeast-2:899673281251:secret:ai-video-gemini-key`
   - ✅ Correct: `arn:aws:secretsmanager:ap-southeast-2:899673281251:secret:ai-video-gemini-key-a1b2c3`

3. **API key copied incorrectly:**
   - Check for extra spaces, newlines, or missing characters
   - Copy directly from Google AI Studio

4. **Task execution role missing permissions:**
   - Must have `secretsmanager:GetSecretValue` permission
   - Resource should match your secret ARN pattern

## Still Not Working?

1. **Verify API key is valid:**
   ```bash
   # Test the API key directly
   curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_API_KEY"
   ```

2. **Check if API key has restrictions:**
   - Go to Google AI Studio
   - Check if API key has IP restrictions or other limitations
   - Ensure it's enabled for the Gemini API

3. **Review CloudWatch logs:**
   - Check for any error messages about secret retrieval
   - Look for the "Gemini API Key loaded" message

