import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_DETAILS = "mongodb+srv://Mamidipaka_Bhagavan_Vara_Prasad:bharath%400712@cluster0.v3qjbj6.mongodb.net/student_collab_hub?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client["student_collab_hub"]
groups_collection = database.get_collection("groups")

def generate_files(base_name, prefix):
    return [
        {
            "id": f"{prefix}-{i+1}",
            "name": f"{base_name}{'' if i == 0 else f'_{i+1}'}.pdf",
            "type": "pdf",
            "url": f"/api/files/{base_name}{'' if i == 0 else f'_' + str(i+1)}.pdf"
        }
        for i in range(8)
    ]

mock_groups = [
    {
        "name": "AI Study Group",
        "description": "Discuss and learn about Artificial Intelligence.",
        "department": "Computer Science and Engineering",
        "year": "3rd Year",
        "interest": "AI",
        "tags": ["AI", "ML", "Python"],
        "files": generate_files("AI_ArtificialIntelligence", "ai-artificial-intelligence"),
    },
    {
        "name": "Code Masters",
        "description": "Competitive programming and coding challenges.",
        "department": "Computer Science and Engineering",
        "year": "4th Year",
        "interest": "Coding",
        "tags": ["Coding", "DSA", "Contests"],
        "files": generate_files("CodeMasters_ComputerScienceAI", "codemasters-ai-paper"),
    },
    {
        "name": "Quantum Quest",
        "description": "Quantum computing and futuristic tech.",
        "department": "Computer Science and Engineering",
        "year": "2nd Year",
        "interest": "Quantum",
        "tags": ["Quantum", "Physics", "Research"],
        "files": generate_files("QuantumComputing", "quantum-computing"),
    },
    {
        "name": "Web Wizards",
        "description": "Frontend, backend, and full-stack web development.",
        "department": "Computer Science and Engineering",
        "year": "3rd Year",
        "interest": "Web",
        "tags": ["React", "Node", "Web"],
        "files": generate_files("WebDevelopment", "web-development"),
    },
    {
        "name": "App Dev Club",
        "description": "Mobile app development for Android and iOS.",
        "department": "Computer Science and Engineering",
        "year": "2nd Year",
        "interest": "Apps",
        "tags": ["Android", "iOS", "Flutter"],
        "files": generate_files("MobileAppDevelopment", "mobile-app-development"),
    },
    {
        "name": "First Year Forum",
        "description": "Support and resources for first-year students.",
        "department": "Computer Science and Engineering",
        "year": "1st Year",
        "interest": "Support",
        "tags": ["Freshers", "Help", "Resources"],
        "files": generate_files("FirstYearCS", "first-year-cs"),
    },
    {
        "name": "Data Science Hub",
        "description": "Explore data analysis, visualization, and big data.",
        "department": "Computer Science and Engineering",
        "year": "4th Year",
        "interest": "Data",
        "tags": ["Data", "Analytics", "Big Data"],
        "files": generate_files("DataScience", "data-science"),
    },
    {
        "name": "Cyber Security Cell",
        "description": "Learn about ethical hacking and security.",
        "department": "Computer Science and Engineering",
        "year": "3rd Year",
        "interest": "Security",
        "tags": ["Security", "Hacking", "Ethical"],
        "files": generate_files("CyberSecurity", "cyber-security"),
    },
    {
        "name": "Open Source Society",
        "description": "Contribute to open source projects.",
        "department": "Computer Science and Engineering",
        "year": "2nd Year",
        "interest": "Open Source",
        "tags": ["GitHub", "OSS", "Projects"],
        "files": generate_files("OpenSourceSoftware", "open-source-software"),
    },
    {
        "name": "Cloud Computing Club",
        "description": "Explore AWS, Azure, and cloud technologies.",
        "department": "Computer Science and Engineering",
        "year": "4th Year",
        "interest": "Cloud",
        "tags": ["AWS", "Azure", "Cloud"],
        "files": generate_files("CloudComputing", "cloud-computing"),
    },
    {
        "name": "Robotics Club",
        "description": "Build and program robots together.",
        "department": "Mechanical Engineering",
        "year": "2nd Year",
        "interest": "Robotics",
        "tags": ["Robotics", "Arduino"],
        "files": generate_files("Robotics", "robotics"),
    },
    {
        "name": "Machine Learning Circle",
        "description": "Deep dive into ML algorithms and projects.",
        "department": "Computer Science and Engineering",
        "year": "3rd Year",
        "interest": "ML",
        "tags": ["ML", "AI", "Projects"],
        "files": [{
            "id": "ml-paper",
            "name": "DataScience.pdf",
            "type": "pdf",
            "url": "/api/files/DataScience.pdf",
        }],
    },
    {
        "name": "Blockchain Innovators",
        "description": "Explore blockchain technology and smart contracts.",
        "department": "Computer Science and Engineering",
        "year": "4th Year",
        "interest": "Blockchain",
        "tags": ["Blockchain", "Crypto", "Smart Contracts"],
        "files": [{
            "id": "blockchain-paper",
            "name": "OpenSourceSoftware.pdf",
            "type": "pdf",
            "url": "/api/files/OpenSourceSoftware.pdf",
        }],
    },
    {
        "name": "AR/VR Enthusiasts",
        "description": "Augmented and Virtual Reality club for creative minds.",
        "department": "Computer Science and Engineering",
        "year": "2nd Year",
        "interest": "AR/VR",
        "tags": ["AR", "VR", "Unity"],
        "files": [{
            "id": "arvr-paper",
            "name": "WebDevelopment.pdf",
            "type": "pdf",
            "url": "/api/files/WebDevelopment.pdf",
        }],
    },
    {
        "name": "Green Tech Forum",
        "description": "Discuss sustainable technology and green energy.",
        "department": "Mechanical Engineering",
        "year": "3rd Year",
        "interest": "Green Tech",
        "tags": ["Sustainability", "Energy", "Environment"],
        "files": [{
            "id": "greentech-paper",
            "name": "CloudComputing.pdf",
            "type": "pdf",
            "url": "/api/files/CloudComputing.pdf",
        }],
    },
    {
        "name": "Quantum Computing Society",
        "description": "Learn and collaborate on quantum computing projects.",
        "department": "Physics",
        "year": "4th Year",
        "interest": "Quantum",
        "tags": ["Quantum", "Physics", "Qubit"],
        "files": [{
            "id": "quantum-paper",
            "name": "QuantumComputing.pdf",
            "type": "pdf",
            "url": "/api/files/QuantumComputing.pdf",
        }],
    },
]

# Add a default member to each group
for group in mock_groups:
    group["members"] = [{"name": "Demo Student", "email": "demo@studentcollab.com"}]

async def seed():
    await groups_collection.delete_many({})  # Optional: clear existing groups
    await groups_collection.insert_many(mock_groups)
    print(f"Inserted {len(mock_groups)} groups.")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed()) 