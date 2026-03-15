# Connecting to SonarCloud

These instructions apply to all four language examples in this repository.

---

## 1. Get your credentials

1. Go to [sonarcloud.io](https://sonarcloud.io) and log in
2. Click your avatar (top right) → **My Account** → **Security**
3. Under **Generate Tokens**, give it a name (e.g. `fitness-functions`) and click **Generate**
4. Copy the token — you only see it once

---

## 2. Find your organization key

Go to `sonarcloud.io/organizations` → your org → **Administration**. The key appears in the URL and on the page. It is usually your GitHub username or organization name.

---

## 3. Create projects in SonarCloud

For each language example you want to scan, create a project manually:

1. Click **+** → **Analyze new project** → **Manually**
2. Select your organization
3. Set the **Project key** to exactly match the value in the example's `sonar-project.properties`:

| Example | Project key |
|---|---|
| Python | `fitness-functions-python-logging` |
| Java | `fitness-functions-java-logging` |
| Node | `fitness-functions-node-logging` |
| .NET | `fitness-functions-dotnet-logging` |

---

## 4. Set your organization key in each sonar-project.properties

Replace `YOUR_ORG_KEY` with your actual organization key in each of these files:

- [Python/logging-standards/sonar-project.properties](Python/logging-standards/sonar-project.properties)
- [Java/logging-standards/sonar-project.properties](Java/logging-standards/sonar-project.properties)
- [Node/logging-standards/sonar-project.properties](Node/logging-standards/sonar-project.properties)
- [.Net/logging-standards/sonar-project.properties](.Net/logging-standards/sonar-project.properties)

Each file already contains:

```properties
sonar.organization=YOUR_ORG_KEY
sonar.host.url=https://sonarcloud.io
```

---

## 5. Install sonar-scanner

```bash
# macOS
brew install sonar-scanner

# Linux
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-6.1.0.4477-linux.zip
unzip sonar-scanner-cli-*.zip
export PATH="$PWD/sonar-scanner-6.1.0.4477-linux/bin:$PATH"
```

---

## 6. Run a scan locally

Pass your token on the command line. Never commit it to the repository.

### Python

```bash
cd Python/logging-standards

pip install -e ".[dev]"
pytest tests/ --cov=src --cov-report=xml:coverage.xml

sonar-scanner -Dsonar.token=YOUR_TOKEN_HERE
```

### Java

```bash
cd Java/logging-standards

mvn clean verify   # generates JaCoCo report at target/site/jacoco/jacoco.xml

sonar-scanner -Dsonar.token=YOUR_TOKEN_HERE
```

### Node

```bash
cd Node/logging-standards

npm install
NODE_ENV=test npx jest --coverage   # generates coverage/lcov.info

sonar-scanner -Dsonar.token=YOUR_TOKEN_HERE
```

### .NET

```bash
cd .Net/logging-standards

dotnet test \
  --collect:"XPlat Code Coverage" \
  --results-directory TestResults \
  -- DataCollectionRunSettings.DataCollectors.DataCollector.Configuration.Format=opencover

sonar-scanner -Dsonar.token=YOUR_TOKEN_HERE
```

---

## 7. Register custom metrics (one-time, admin)

Before the quality gate can block on `logging_violations`, you need to register the custom metric definitions:

```bash
export SONAR_URL=https://sonarcloud.io
export SONAR_TOKEN=your_token_here
./scripts/setup_sonarqube_metrics.sh
```

> **Note:** Custom metrics via the API require the **Developer Edition** or higher on SonarQube Server. On SonarCloud, custom measures are not currently supported via API. You can still use all built-in metrics (coverage, security rating, bugs, etc.) in your quality gate — the `logging_violations` custom metric push is optional for the free tier.

---

## 8. View trend data

After at least two scans have run:

```bash
export SONAR_URL=https://sonarcloud.io
export SONAR_TOKEN=your_token_here

python scripts/trend_report.py --project fitness-functions-python-logging --days 30
```

---

## 9. GitHub Actions (automated scanning)

Add two repository secrets under **Settings → Secrets and variables → Actions**:

| Secret name | Value |
|---|---|
| `SONAR_TOKEN` | your token from step 1 |
| `SONAR_HOST_URL` | `https://sonarcloud.io` |

The workflow file at [Python/logging-standards/.github/workflows/fitness-python-logging.yml](Python/logging-standards/.github/workflows/fitness-python-logging.yml) is already configured to use these secrets and will run on every push to `main` and weekly on a schedule.

---

## Quick reference

| Variable | Value |
|---|---|
| `SONAR_URL` | `https://sonarcloud.io` |
| `SONAR_TOKEN` | your personal or CI token |
| `sonar.organization` | your org key (e.g. `michaelmccabe`) |
| `sonar.host.url` | `https://sonarcloud.io` |
