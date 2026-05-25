class RoleLibrary:
    """Curated collection of industry-standard job description templates."""

    TEMPLATES = {
        # --- Engineering ---
        "Full Stack Developer": """We are looking for a Full Stack Developer to build robust web applications.
Core Requirements:
- Foundational skills in frontend (React, Vue, HTML5, CSS3) and backend (Python Flask/FastAPI, Node.js, or Go)
- Deep understanding of Databases (SQL, PostgreSQL, MongoDB) and API development (REST, GraphQL)
- Experience with cloud infrastructure (AWS/GCP), containerization (Docker, Kubernetes), and CI/CD pipelines
- Strong optimization, clean code patterns, and unit testing focus.""",

        "Frontend Engineer": """We are seeking a Frontend Engineer obsessed with responsive layouts and pixel-perfect UIs.
Core Requirements:
- Mastery of JavaScript (ES6+), TypeScript, and React.js/Next.js ecosystem
- Advanced CSS styling skills (Tailwind CSS, CSS modules, styling design systems, or Vanilla CSS)
- Experience with state management (Redux, Zustand) and client performance optimization
- Familiarity with build tools like Vite, Webpack, and browser testing/rendering pipelines.""",

        "Backend Engineer": """We are looking for a Backend Engineer to design and maintain high-performance, secure server infrastructure.
Core Requirements:
- Expert programming in Python, Go, Java, or Node.js
- Experience designing scalable relational databases (PostgreSQL) and caching layers (Redis)
- Solid grasp of microservices architecture, message queues (RabbitMQ, Kafka), and RESTful APIs
- Strong security practices, data encryption, input validation, and secure authentication schemas.""",

        "DevOps Engineer": """We are looking for a DevOps Engineer to automate and scale our cloud deployment pipelines.
Core Requirements:
- Infrastructure as Code (IaC) mastery using Terraform or CloudFormation
- Container orchestration with Kubernetes, Docker, and cloud platforms (AWS, GCP, or Azure)
- Setting up automated CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- Implementing system observability, structured logging, and monitoring (Prometheus, Grafana).""",

        # --- Data & AI ---
        "Data Scientist": """We are seeking a Data Scientist to extract actionable insights from large datasets.
Core Requirements:
- Strong foundations in Python/R programming, SQL, and database querying
- Solid understanding of statistical analysis, regression, hypothesis testing, and quantitative modeling
- Mastery of data science libraries (Pandas, NumPy, Scikit-Learn, Statsmodels)
- Experience with data visualization tools (Tableau, PowerBI) and presenting findings to business stakeholders.""",

        "Machine Learning Engineer": """We are looking for a Machine Learning Engineer to deploy state-of-the-art predictive algorithms.
Core Requirements:
- Python programming with strong clean code standards
- Direct experience building, training, and optimizing deep learning models (PyTorch, TensorFlow)
- Knowledge of machine learning system deployment (MLOps, MLflow, BentoML)
- Understanding of feature engineering, model validation techniques, and vector databases (Qdrant, Pinecone).""",

        # --- Product & Design ---
        "Product Manager": """We are looking for an analytical, user-focused Product Manager to drive product delivery.
Core Requirements:
- Strong track record defining product roadmaps, PRDs, and user story definitions
- Analytical mindset with metric-driven approaches (A/B testing, SQL analytics, Mixpanel)
- Solid interface design sensibilities and translating complex criteria to developers
- Exceptional communication, cross-functional collaboration, and agile delivery skills.""",

        "UX/UI Designer": """We are seeking a UX/UI Designer to craft engaging, accessible user experiences.
Core Requirements:
- Expert design skills in Figma (components, autolayout, design system libraries)
- Deep understanding of user research, wireframing, high-fidelity mockups, and prototyping
- Knowledge of accessibility standards (WCAG) and responsive web grid principles
- Experience working closely with developers to deliver clean asset handoffs.""",

        # --- Marketing & Sales ---
        "Digital Marketing Manager": """We are looking for a Digital Marketing Manager to scale our acquisition channels.
Core Requirements:
- Strategic execution of search engine optimization (SEO) and paid acquisition (Google Ads, Meta Ads)
- Analytical monitoring of traffic conversion using Google Analytics 4, Mixpanel, or similar
- Copywriting, content marketing strategy, and marketing automation email sequences
- Strong A/B testing framework and optimizing customer acquisition cost (CAC).""",

        "Sales Representative": """We are seeking a high-performing Sales Representative to generate pipeline and close deals.
Core Requirements:
- Excellent communication, outbound cold calling, and relationship management skills
- Expert pipeline tracking using CRMs (HubSpot, Salesforce)
- Strategic value-based selling, conducting product demos, and negotiating terms
- Consistent track record of meeting or exceeding quarterly quotas.""",

        # --- Analytics ---
        "Data Analyst": """We are looking for a Data Analyst to transform raw datasets into actionable business intelligence.
Core Requirements:
- Advanced proficiency in SQL, Excel/Google Sheets, and Python for data wrangling
- Expertise with BI visualization tools (Tableau, PowerBI, Looker)
- Statistical analysis skills: regression, A/B testing, cohort analysis
- Strong storytelling ability to present data-driven insights to non-technical stakeholders.""",

        # --- Security ---
        "Cybersecurity Analyst": """We are looking for a Cybersecurity Analyst to protect organizational systems and data assets.
Core Requirements:
- Deep understanding of network security, firewalls, IDS/IPS, and SIEM platforms (Splunk, CrowdStrike)
- Hands-on experience with vulnerability assessments, penetration testing, and incident response
- Knowledge of compliance frameworks (ISO 27001, NIST, SOC 2, GDPR)
- Proficiency in scripting (Python, Bash) for security automation and threat hunting.""",

        # --- Cloud & Infrastructure ---
        "Cloud Architect": """We are seeking a Cloud Architect to design resilient, cost-optimized cloud infrastructure.
Core Requirements:
- Multi-cloud expertise across AWS, Azure, or GCP (certifications preferred: AWS SA-Pro, GCP PCA)
- Designing highly-available distributed systems using microservices, serverless, and event-driven architectures
- Infrastructure as Code (Terraform, Pulumi) and GitOps deployment pipelines
- Cost optimization, FinOps practices, and cloud security best practices (IAM, VPC, encryption).""",

        # --- Mobile ---
        "Mobile Developer": """We are seeking a Mobile Developer to build high-performance cross-platform mobile applications.
Core Requirements:
- Expert-level React Native, Flutter, or native iOS (Swift) / Android (Kotlin) development
- Deep knowledge of mobile UI/UX patterns, animations, and responsive layouts
- Experience with mobile backend integrations (REST APIs, Firebase, GraphQL)
- App store deployment workflows, CI/CD for mobile (Fastlane), and crash analytics (Sentry, Crashlytics).""",

        # --- Quality Assurance ---
        "QA Engineer": """We are looking for a QA Engineer to build and maintain comprehensive automated test suites.
Core Requirements:
- Strong experience with test automation frameworks (Selenium, Cypress, Playwright, Appium)
- Proficiency in writing unit, integration, and end-to-end tests with clear coverage strategies
- API testing expertise (Postman, REST Assured) and performance testing (JMeter, k6)
- Understanding of CI/CD integration for continuous quality gates and regression testing.""",

        # --- Business ---
        "Business Analyst": """We are seeking a Business Analyst to bridge the gap between stakeholders and technical teams.
Core Requirements:
- Strong requirements gathering, user story writing, and business process modeling (BPMN)
- Proficiency with data analysis tools (SQL, Excel, Jira, Confluence)
- Experience with Agile/Scrum methodologies and sprint planning facilitation
- Excellent communication skills for stakeholder management and UAT coordination."""
    }

    @classmethod
    def get_list(cls):
        """Returns categories and profiles names."""
        return list(cls.TEMPLATES.keys())

    @classmethod
    def get_template(cls, role_name: str) -> str:
        """Returns the JD text template for a specific role name."""
        return cls.TEMPLATES.get(role_name, "")
