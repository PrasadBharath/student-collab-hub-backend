from fastapi import FastAPI, Body, HTTPException, status, Depends, Header, Path, UploadFile, File, Form, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import random
from typing import Optional, List, Any
from fastapi.responses import FileResponse
import os
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# --- Cloudinary Integration ---
import cloudinary
import cloudinary.uploader
cloudinary.config(
    cloud_name="dtrdvg0up",  # or use os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key="513448789942263",
    api_secret="un7mSYczC7S5HD-m-EaJ0xWyakE"
)

import logging
# --- Posts and Comments Models ---
# --- Activity Logging Helper ---
async def log_activity(user_email: str, action: str, details: dict = None):
    try:
        log_entry = {
            "user": user_email,
            "action": action,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        await activitylog_collection.insert_one(log_entry)
    except Exception as e:
        logging.error(f"Failed to log activity: {e}")
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import List, Optional, Any

class CommentModel(BaseModel):
    id: Optional[Any] = Field(default_factory=lambda: str(ObjectId()))
    user: str
    text: str
    replies: List[Any] = Field(default_factory=list)

class PostModel(BaseModel):
    id: Optional[Any] = Field(default_factory=lambda: str(ObjectId()))
    type: str
    title: str
    content: str
    tags: List[str] = Field(default_factory=list)
    fileUrl: Optional[str] = None
    jobLink: Optional[str] = None
    referrals: Optional[str] = None
    author: str
    comments: List[Any] = Field(default_factory=list)
    createdAt: Optional[str] = None

class ActivityLog(BaseModel):
    id: Optional[Any] = Field(default_factory=lambda: str(ObjectId()))
    user: str
    action: str
    details: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

app = FastAPI()

# CORS middleware should be right after app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://aesthetic-squirrel-765c27.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup (move this block here)
MONGO_DETAILS = "mongodb+srv://Mamidipaka_Bhagavan_Vara_Prasad:bharath%400712@cluster0.v3qjbj6.mongodb.net/student_collab_hub?retryWrites=true&w=majority&appName=Cluster0"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client["student_collab_hub"]
users_collection = database.get_collection("users")
groups_collection = database.get_collection("groups")
schedule_collection = database.get_collection("schedule")
resources_collection = database.get_collection("resources")
blogs_collection = database.get_collection("blogs")
posts_collection = database.get_collection("posts")
activitylog_collection = database.get_collection("activitylog")

# Password hashing (move this block up)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings (move this block up)
SECRET_KEY = os.getenv('SECRET_KEY')  # Change this to a strong secret in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Path to the React build directory
build_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'frontend-build'))

# Place get_current_user here, before any FastAPI app or route definitions
async def get_current_user(Authorization: Optional[str] = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = Authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await users_collection.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: str
    department: str
    year: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOtpRequest(BaseModel):
    email: EmailStr
    new_password: str
    otp: str = ''

class ScheduleEvent(BaseModel):
    title: str
    description: Optional[str] = ""
    start: str
    end: str
    type: str
    group: Optional[str] = ""
    notification: Optional[bool] = False
    completed: Optional[bool] = False

class BlogPost(BaseModel):
    title: str
    content: str
    date: Optional[str] = None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

auth_router = APIRouter(prefix="/api/auth")

@auth_router.post("/login", response_model=Token)
async def api_login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@auth_router.post("/register", status_code=201)
async def api_register(user: UserCreate):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_pw
    await users_collection.insert_one(user_dict)
    return {"msg": "User registered successfully"}

app.include_router(auth_router)

@app.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    email = request.email
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # No email/OTP logic, just return success for demo
    return {"msg": "If this email exists, you can reset your password (demo)."}

@app.post("/verify-otp")
async def verify_otp(request: VerifyOtpRequest):
    email = request.email
    new_password = request.new_password
    user = await users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    hashed_pw = get_password_hash(new_password)
    await users_collection.update_one({"email": email}, {"$set": {"password": hashed_pw}})
    return {"msg": "Password reset successful (demo)"}

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    year: Optional[str] = None
    skills: Optional[List[str]] = None
    role: Optional[str] = None

def fix_mongo_ids(obj):
    if isinstance(obj, list):
        return [fix_mongo_ids(item) for item in obj]
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k == "_id":
                new["id"] = str(v)
            elif isinstance(v, ObjectId):
                new[k] = str(v)
            else:
                new[k] = fix_mongo_ids(v)
        return new
    return obj

@app.get("/users/me")
async def get_me(user=Depends(get_current_user)):
    user = fix_mongo_ids(user)
    user.pop("password", None)
    return {"user": user}

@app.put("/users/me")
async def update_me(update: UserUpdate, user=Depends(get_current_user)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    # If email is being updated, check for uniqueness
    if "email" in update_data and update_data["email"] != user["email"]:
        existing = await users_collection.find_one({"email": update_data["email"]})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    await users_collection.update_one({"email": user["email"]}, {"$set": update_data})
    user.update(update_data)
    user = fix_mongo_ids(user)
    user.pop("password", None)
    return {"user": user}

@app.put("/api/users/profile")
async def update_profile(update: UserUpdate, user=Depends(get_current_user)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if "email" in update_data and update_data["email"] != user["email"]:
        existing = await users_collection.find_one({"email": update_data["email"]})
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
    await users_collection.update_one({"email": user["email"]}, {"$set": update_data})
    user.update(update_data)
    user = fix_mongo_ids(user)
    user.pop("password", None)
    return {"user": user}

@app.get("/api/auth/me")
async def get_auth_me(user=Depends(get_current_user)):
    user = fix_mongo_ids(user)
    user.pop("password", None)
    return {"user": user}

@app.get("/api/users/profile")
async def get_profile(user=Depends(get_current_user)):
    user = fix_mongo_ids(user)
    user.pop("password", None)
    return {"user": user}

@app.post("/api/schedule")
async def add_schedule(event: ScheduleEvent, user=Depends(get_current_user)):
    event_dict = event.dict()
    event_dict["user"] = user["email"]
    result = await schedule_collection.insert_one(event_dict)
    event_dict["_id"] = str(result.inserted_id)
    return {"meeting": event_dict}

@app.get("/api/schedule")
async def get_schedule(user=Depends(get_current_user)):
    meetings = []
    async for meeting in schedule_collection.find({"user": user["email"]}):
        meetings.append(fix_mongo_ids(meeting))
    return {"meetings": meetings}

@app.patch("/api/schedule/{id}")
async def update_schedule(id: str, event: ScheduleEvent, user=Depends(get_current_user)):
    update_data = {k: v for k, v in event.dict().items() if v is not None}
    result = await schedule_collection.update_one({"_id": __import__("bson").ObjectId(id), "user": user["email"]}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting = await schedule_collection.find_one({"_id": __import__("bson").ObjectId(id)})
    meeting["_id"] = str(meeting["_id"])
    return {"message": "Meeting updated successfully", "meeting": fix_mongo_ids(meeting)}

@app.delete("/api/schedule/{id}")
async def delete_schedule(id: str, user=Depends(get_current_user)):
    result = await schedule_collection.delete_one({"_id": __import__("bson").ObjectId(id), "user": user["email"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"message": "Meeting deleted successfully"}

@app.get("/files/{filename}")
async def get_private_file(filename: str, user=Depends(get_current_user)):
    # Only allow access to files in the private-files directory
    file_path = os.path.join(os.path.dirname(__file__), "private-files", filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

@app.post("/groups/{group_id}/join")
async def join_group(group_id: str = Path(...), user=Depends(get_current_user)):
    group = await groups_collection.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    members = group.get("members", [])
    if any(m.get("email") == user["email"] for m in members):
        return {"msg": "Already a member"}
    members.append({"email": user["email"], "name": user.get("name", user["email"])} )
    await groups_collection.update_one({"_id": ObjectId(group_id)}, {"$set": {"members": members}})
    # Add group to user's groups array
    user_groups = user.get("groups", [])
    if group_id not in user_groups:
        user_groups.append(group_id)
        await users_collection.update_one({"email": user["email"]}, {"$set": {"groups": user_groups}})
    return {"msg": "Joined group successfully"}

@app.post("/groups/{group_id}/leave")
async def leave_group(group_id: str = Path(...), user=Depends(get_current_user)):
    group = await groups_collection.find_one({"_id": ObjectId(group_id)})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    members = group.get("members", [])
    new_members = [m for m in members if m.get("email") != user["email"]]
    await groups_collection.update_one({"_id": ObjectId(group_id)}, {"$set": {"members": new_members}})
    # Remove group from user's groups array
    user_groups = user.get("groups", [])
    if group_id in user_groups:
        user_groups = [gid for gid in user_groups if gid != group_id]
        await users_collection.update_one({"email": user["email"]}, {"$set": {"groups": user_groups}})
    return {"msg": "Left group successfully"}

@app.get("/api/files/{filename}")
async def get_group_file(filename: str, user=Depends(get_current_user)):
    file_path = os.path.join(os.path.dirname(__file__), "group-files", filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)

# Ensure resources-files directory exists
resources_dir = os.path.join(os.path.dirname(__file__), "resources-files")
os.makedirs(resources_dir, exist_ok=True)

# Resource model for MongoDB
# Fields: name, description, type, url, uploadedBy, uploadedAt, size, groupId (optional)

@app.post("/api/resources")
async def upload_resource(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    groupId: str = Form(None),
    user=Depends(get_current_user)
):
    # Save file to disk
    file_location = os.path.join(resources_dir, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    # Build resource metadata
    resource = {
        "name": name,
        "description": description,
        "type": file.content_type,
        "url": f"/api/files/{file.filename}",
        "uploadedBy": user["email"],
        "uploadedAt": datetime.utcnow(),
        "size": os.path.getsize(file_location),
        "filename": file.filename,
    }
    if groupId:
        resource["groupId"] = groupId
    result = await resources_collection.insert_one(resource)
    resource["_id"] = str(result.inserted_id)
    return {"resource": resource}

@app.get("/api/resources")
async def list_resources(type: str = None, groupId: str = None, user=Depends(get_current_user)):
    query = {}
    if type:
        query["type"] = type
    if groupId:
        query["groupId"] = groupId
    resources = []
    async for res in resources_collection.find(query):
        resources.append(fix_mongo_ids(res))
    return {"resources": resources}

@app.get("/api/resources/{resource_id}")
async def get_resource(resource_id: str, user=Depends(get_current_user)):
    res = await resources_collection.find_one({"_id": ObjectId(resource_id)})
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")
    return {"resource": fix_mongo_ids(res)}

@app.get("/blogs")
async def list_blogs(user=Depends(get_current_user)):
    blogs = []
    async for blog in blogs_collection.find().sort("_id", -1):
        blog["likes"] = blog.get("likes", [])
        blog["like_count"] = len(blog["likes"])
        blog["liked"] = user["email"] in blog["likes"]
        blogs.append(fix_mongo_ids(blog))
    return {"blogs": blogs}

@app.get("/blogs/{id}")
async def get_blog(id: str, user=Depends(get_current_user)):
    blog = await blogs_collection.find_one({"_id": ObjectId(id)})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    blog["likes"] = blog.get("likes", [])
    blog["like_count"] = len(blog["likes"])
    blog["liked"] = user["email"] in blog["likes"]
    return {"blog": fix_mongo_ids(blog)}

@app.post("/blogs/{id}/like")
async def like_blog(id: str, user=Depends(get_current_user)):
    blog = await blogs_collection.find_one({"_id": ObjectId(id)})
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    likes = blog.get("likes", [])
    user_email = user["email"]
    if user_email in likes:
        # Unlike
        likes = [email for email in likes if email != user_email]
        liked = False
    else:
        # Like
        likes.append(user_email)
        liked = True
    await blogs_collection.update_one({"_id": ObjectId(id)}, {"$set": {"likes": likes}})
    return {"liked": liked, "like_count": len(likes)}

@app.post("/blogs")
async def create_blog(post: BlogPost, user=Depends(get_current_user)):
    blog = jsonable_encoder(post)
    blog["author"] = user.get("name", user["email"])
    blog["author_email"] = user["email"]
    blog["date"] = post.date or datetime.utcnow().isoformat()
    blog["likes"] = []
    result = await blogs_collection.insert_one(blog)
    blog["_id"] = str(result.inserted_id)
    return {"blog": blog}

sample_blogs = [
    {
        "title": "The Future of Artificial Intelligence in Engineering",
        "author": "Dr. A. Sharma",
        "date": "2024-05-01T10:00:00Z",
        "content": "Artificial Intelligence (AI) is rapidly transforming the engineering landscape. From automating repetitive tasks to enabling predictive maintenance, AI is making engineering processes more efficient and reliable. Machine learning algorithms can analyze vast amounts of data to identify patterns and optimize system performance.\n\nAI-driven design tools are helping engineers create more innovative products by simulating thousands of design variations in seconds. This accelerates the prototyping process and reduces costs.\n\nIn civil engineering, AI is used for structural health monitoring and smart city planning. Sensors embedded in bridges and buildings collect data that AI systems analyze to predict maintenance needs and prevent failures.\n\nElectrical engineering is also benefiting from AI, especially in the development of smart grids. These grids use AI to balance energy loads, detect outages, and integrate renewable energy sources more effectively.\n\nMechanical engineers are leveraging AI for predictive maintenance in manufacturing plants. By analyzing sensor data, AI can forecast equipment failures and schedule repairs before breakdowns occur.\n\nAI is revolutionizing robotics, enabling machines to learn from their environment and adapt to new tasks. This is particularly useful in hazardous environments where human intervention is risky.\n\nThe integration of AI with the Internet of Things (IoT) is creating intelligent systems that can monitor and control complex engineering processes remotely.\n\nAI is also playing a crucial role in environmental engineering by modeling climate change scenarios and optimizing resource usage for sustainability.\n\nAs AI continues to evolve, engineers must adapt by learning new tools and integrating AI into their workflows for better outcomes. The future of engineering will be shaped by those who can harness the power of AI to solve complex problems.\n\nContinuous learning and collaboration between AI experts and engineers will be essential to unlock the full potential of this transformative technology.",
    },
    {
        "title": "Sustainable Civil Engineering: Green Building Trends",
        "author": "Prof. K. Gupta",
        "date": "2024-04-18T09:00:00Z",
        "content": "Sustainability is at the forefront of modern civil engineering. Green building trends focus on reducing environmental impact through the use of eco-friendly materials, energy-efficient designs, and renewable energy sources. LEED certification and other green standards are becoming increasingly important in the construction industry.\n\nCivil engineers are now designing buildings that use less water, generate less waste, and have a smaller carbon footprint. The integration of smart technologies, such as automated lighting and climate control, further enhances building sustainability.\n\nRecycled materials like fly ash and slag are being used in concrete to reduce the demand for virgin resources. Green roofs and walls are also gaining popularity for their ability to insulate buildings and improve air quality.\n\nEnergy modeling software allows engineers to simulate building performance and optimize designs for maximum efficiency. This helps in achieving net-zero energy buildings.\n\nWater conservation is another key aspect, with engineers implementing rainwater harvesting and greywater recycling systems in new constructions.\n\nThe use of renewable energy sources, such as solar panels and wind turbines, is becoming standard practice in green building projects.\n\nSmart sensors and building management systems enable real-time monitoring of energy and water usage, allowing for continuous optimization.\n\nSustainable urban planning involves creating walkable neighborhoods, promoting public transportation, and preserving green spaces.\n\nCivil engineers are also addressing the challenges of climate change by designing resilient infrastructure that can withstand extreme weather events.\n\nEducation and awareness are crucial for the widespread adoption of green building practices. Engineers must stay updated with the latest trends and technologies to lead the way in sustainable development.",
    },
    {
        "title": "Robotics in Mechanical Engineering: The Next Leap",
        "author": "Dr. P. Singh",
        "date": "2024-03-30T14:00:00Z",
        "content": "Robotics is revolutionizing mechanical engineering by automating manufacturing processes and improving precision. Robots are now used for tasks ranging from assembly and welding to quality inspection and packaging. This not only increases productivity but also enhances workplace safety.\n\nRecent advancements in robotics include collaborative robots (cobots) that work alongside humans and adaptive robots that can learn from their environment. The future of mechanical engineering will be shaped by the continued integration of robotics and AI.\n\nRobots equipped with machine vision can inspect products for defects with greater accuracy than human inspectors.\n\nAutomated guided vehicles (AGVs) are streamlining material handling in factories, reducing the need for manual labor.\n\n3D printing robots are enabling the rapid prototyping of complex mechanical parts, accelerating the product development cycle.\n\nRobotics is also making inroads into the healthcare sector, with surgical robots assisting doctors in performing minimally invasive procedures.\n\nThe use of exoskeletons is helping workers lift heavy objects safely, reducing the risk of injury.\n\nResearch in soft robotics is leading to the development of flexible robots that can navigate challenging environments.\n\nMechanical engineers are collaborating with computer scientists to develop advanced control algorithms for autonomous robots.\n\nThe integration of robotics with IoT is enabling remote monitoring and control of robotic systems, opening up new possibilities for automation.",
    },
    {
        "title": "Emerging Technologies in Electrical Engineering",
        "author": "Dr. R. Verma",
        "date": "2024-03-15T11:00:00Z",
        "content": "Electrical engineering is experiencing a wave of innovation with the rise of smart grids, renewable energy, and the Internet of Things (IoT). Smart grids use digital technology to monitor and manage electricity flow, making energy distribution more efficient and reliable.\n\nIoT devices are enabling real-time monitoring and control of electrical systems in homes and industries. As renewable energy sources like solar and wind become more prevalent, electrical engineers are developing new solutions for energy storage and grid integration.\n\nThe adoption of electric vehicles (EVs) is driving the need for advanced charging infrastructure and grid management solutions.\n\nWireless power transfer is becoming a reality, with engineers developing systems to charge devices without physical connections.\n\nMicrogrids are providing localized energy solutions for remote areas and critical facilities.\n\nThe integration of artificial intelligence with electrical systems is enabling predictive maintenance and fault detection.\n\nSmart meters are giving consumers greater control over their energy usage, promoting energy conservation.\n\nThe development of high-efficiency solar panels and wind turbines is making renewable energy more accessible and affordable.\n\nCybersecurity is a growing concern in electrical engineering, with engineers working to protect critical infrastructure from cyber threats.\n\nContinuous research and innovation are essential to keep pace with the rapidly evolving field of electrical engineering.",
    },
    {
        "title": "The Role of Data Science in Modern Engineering",
        "author": "Dr. M. Iyer",
        "date": "2024-02-20T13:00:00Z",
        "content": "Data science is becoming an essential skill for engineers across all disciplines. By leveraging big data analytics, engineers can make more informed decisions, optimize designs, and predict system failures before they occur.\n\nApplications of data science in engineering include predictive maintenance, quality control, and process optimization. Learning programming languages like Python and tools like TensorFlow can give engineers a competitive edge in the job market.\n\nEngineers are using data visualization tools to communicate complex information clearly and effectively.\n\nMachine learning models are being applied to optimize supply chains and reduce operational costs.\n\nSensor data from industrial equipment is analyzed to detect anomalies and prevent breakdowns.\n\nData-driven decision-making is improving the efficiency of construction projects and resource allocation.\n\nThe integration of data science with IoT is enabling real-time monitoring and control of engineering systems.\n\nEngineers are collaborating with data scientists to develop custom algorithms for specific engineering challenges.\n\nContinuous learning and upskilling in data science are crucial for engineers to stay relevant in the digital age.\n\nEthical considerations, such as data privacy and security, must be addressed when implementing data-driven solutions.",
    },
    {
        "title": "Quantum Computing: The Next Frontier for Engineers",
        "author": "Dr. S. Rao",
        "date": "2024-01-25T15:00:00Z",
        "content": "Quantum computing promises to solve complex engineering problems that are currently intractable for classical computers. With the ability to process vast amounts of data simultaneously, quantum computers could revolutionize fields like cryptography, materials science, and optimization.\n\nEngineers are now exploring quantum algorithms and hardware, preparing for a future where quantum computing becomes mainstream. Staying updated with the latest research in this field is crucial for forward-thinking engineers.\n\nQuantum computers use qubits, which can represent multiple states at once, enabling parallel computation.\n\nQuantum algorithms like Shor's and Grover's are demonstrating the potential to solve problems much faster than classical algorithms.\n\nMaterials science is benefiting from quantum simulations that model molecular interactions with unprecedented accuracy.\n\nOptimization problems in logistics and manufacturing could be solved more efficiently using quantum techniques.\n\nThe field is still in its infancy, but rapid progress is being made by researchers and engineers worldwide.\n\nLearning the basics of quantum mechanics and quantum programming languages like Q# or Qiskit can help engineers prepare for the quantum era.\n\nCollaboration between academia and industry is driving innovation in quantum technologies.\n\nEthical and security considerations will be important as quantum computing becomes more accessible.\n\nEngineers who embrace quantum computing early will be well-positioned to lead in this exciting new frontier."
    },
]

@app.post("/seed-blogs")
async def seed_blogs():
    count = 0
    for post in sample_blogs:
        # Check if a blog with the same title and author already exists
        existing = await blogs_collection.find_one({"title": post["title"], "author": post["author"]})
        if not existing:
            post["likes"] = []
            post["author_email"] = post["author"]
            result = await blogs_collection.insert_one(post)
            count += 1
    return {"seeded": count, "message": f"Seeded {count} blog posts."}

# --- Helper: Populate user info for comments (recursive) ---
async def deep_populate_users(comments):
    populated = []
    for comment in comments:
        user_doc = await users_collection.find_one({"_id": ObjectId(comment["user"])})
        user_info = {"id": str(user_doc["_id"]), "name": user_doc["name"], "avatar": user_doc.get("avatar") } if user_doc else {"name": "User"}
        new_comment = {
            **comment,
            "user": user_info,
            "replies": await deep_populate_users(comment.get("replies", []))
        }
        populated.append(new_comment)
    return populated

# --- Posts Endpoints ---
from fastapi import File, UploadFile, Form
from datetime import datetime

@app.post("/api/posts", response_model=PostModel)
async def create_post(
    type: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    tags: str = Form(""),
    file: UploadFile = File(None),
    jobLink: str = Form(None),
    referrals: str = Form(None),
    user=Depends(get_current_user)
):
    fileUrl = None
    if file:
        upload_result = cloudinary.uploader.upload(file.file, resource_type="raw", folder="student-collab-hub/pdfs/")
        fileUrl = upload_result["secure_url"]
    post = PostModel(
        type=type,
        title=title,
        content=content,
        tags=tags.split(",") if tags else [],
        fileUrl=fileUrl,
        jobLink=jobLink,
        referrals=referrals,
        author=str(user["_id"]),
        createdAt=datetime.utcnow().isoformat()
    )
    post_dict = post.dict()
    post_dict["comments"] = []
    result = await posts_collection.insert_one(post_dict)
    post_dict["_id"] = str(result.inserted_id)
    await log_activity(user["email"], "create_post", {"post_id": post_dict["_id"], "title": title})
    return post_dict

@app.get("/api/posts")
async def get_posts(skip: int = 0, limit: int = 20):
    # Use aggregation pipeline for better performance - single query with lookup
    pipeline = [
        {"$sort": {"createdAt": -1}},
        {"$skip": skip},
        {"$limit": limit},
        {
            "$lookup": {
                "from": "users",
                "localField": "author",
                "foreignField": "_id",
                "as": "author_info"
            }
        },
        {
            "$addFields": {
                "author": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$author_info"}, 0]},
                        "then": {
                            "id": {"$toString": {"$arrayElemAt": ["$author_info._id", 0]}},
                            "name": {"$arrayElemAt": ["$author_info.name", 0]},
                            "department": {"$arrayElemAt": ["$author_info.department", 0]}
                        },
                        "else": {"name": "User"}
                    }
                }
            }
        },
        {"$unset": "author_info"}
    ]
    
    posts = []
    async for post in posts_collection.aggregate(pipeline):
        posts.append(fix_mongo_ids(post))
    return posts

@app.get("/api/posts/{post_id}")
async def get_post(post_id: str):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    author_doc = await users_collection.find_one({"_id": ObjectId(post["author"])})
    post["author"] = {"id": str(author_doc["_id"]), "name": author_doc["name"], "department": author_doc.get("department") } if author_doc else {"name": "User"}
    return fix_mongo_ids(post)

@app.put("/api/posts/{post_id}")
async def update_post(post_id: str, data: dict, user=Depends(get_current_user)):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if str(post["author"]) != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    await posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": data})
    return {"success": True}

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str, user=Depends(get_current_user)):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if str(post["author"]) != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")
    await posts_collection.delete_one({"_id": ObjectId(post_id)})
    await log_activity(user["email"], "delete_post", {"post_id": post_id})
    return {"success": True}

# --- Comments Endpoints (threaded/nested) ---
@app.get("/api/posts/{post_id}/comments")
async def get_comments(post_id: str):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comments = await deep_populate_users(post.get("comments", []))
    return fix_mongo_ids(comments)

@app.post("/api/posts/{post_id}/comments")
async def add_comment(post_id: str, text: str = Form(...), user=Depends(get_current_user)):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = CommentModel(user=str(user["_id"]), text=text).dict()
    post["comments"].append(comment)
    await posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": {"comments": post["comments"]}})
    await log_activity(user["email"], "add_comment", {"post_id": post_id, "comment": text})
    return fix_mongo_ids(await deep_populate_users(post["comments"]))

@app.post("/api/posts/{post_id}/comments/{comment_id}/reply")
async def add_reply(post_id: str, comment_id: str, text: str = Form(...), user=Depends(get_current_user)):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    def add_reply_recursive(comments):
        for comment in comments:
            if str(comment["id"]) == comment_id:
                comment.setdefault("replies", []).append(CommentModel(user=str(user["_id"]), text=text).dict())
                return True
            if "replies" in comment and add_reply_recursive(comment["replies"]):
                return True
        return False
    if not add_reply_recursive(post["comments"]):
        raise HTTPException(status_code=404, detail="Comment not found")
    await posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": {"comments": post["comments"]}})
    return fix_mongo_ids(await deep_populate_users(post["comments"]))

@app.put("/api/posts/{post_id}/comments/{comment_id}")
async def edit_comment(post_id: str, comment_id: str, text: str = Form(...), user=Depends(get_current_user)):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    def edit_recursive(comments):
        for comment in comments:
            if str(comment["id"]) == comment_id:
                if comment["user"] != str(user["_id"]):
                    return 'unauthorized'
                comment["text"] = text
                return True
            if "replies" in comment:
                result = edit_recursive(comment["replies"])
                if result == 'unauthorized':
                    return 'unauthorized'
        return False
    result = edit_recursive(post["comments"])
    if result == 'unauthorized':
        raise HTTPException(status_code=403, detail="Not authorized")
    if not result:
        raise HTTPException(status_code=404, detail="Comment not found")
    await posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": {"comments": post["comments"]}})
    return fix_mongo_ids(await deep_populate_users(post["comments"]))

@app.delete("/api/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: str, comment_id: str, user=Depends(get_current_user)):
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    def delete_recursive(comments):
        for i, comment in enumerate(comments):
            if str(comment["id"]) == comment_id:
                if comment["user"] != str(user["_id"]):
                    return 'unauthorized'
                comments.pop(i)
                return True
            if "replies" in comment:
                result = delete_recursive(comment["replies"])
                if result == 'unauthorized':
                    return 'unauthorized'
        return False
    result = delete_recursive(post["comments"])
    if result == 'unauthorized':
        raise HTTPException(status_code=403, detail="Not authorized")
    if not result:
        raise HTTPException(status_code=404, detail="Comment not found")
    await posts_collection.update_one({"_id": ObjectId(post_id)}, {"$set": {"comments": post["comments"]}})
    return fix_mongo_ids(await deep_populate_users(post["comments"]))

# --- Cloudinary File Download Proxy ---
import requests
@app.get("/api/posts/pdf-proxy/{filename}")
async def pdf_proxy(filename: str):
    cloudinary_url = f"https://res.cloudinary.com/dtrdvg0up/raw/upload/student-collab-hub/pdfs/{filename}"
    r = requests.get(cloudinary_url, stream=True)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="File not found or not accessible")
    from fastapi.responses import StreamingResponse
    return StreamingResponse(r.raw, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

@app.post("/api/admin/add-demo-user")
async def add_demo_user(
    email: str = Query("demo@example.com"),
    name: str = Query("Demo User"),
    password: str = Query("demopass"),
    phone: str = Query("1234567890"),
    department: str = Query("Computer Science"),
    year: str = Query("2nd Year"),
    role: str = Query("Student"),
    skills: str = Query("Web Dev,DSA")
):
    existing = await users_collection.find_one({"email": email})
    if existing:
        return {"msg": "User already exists", "user": fix_mongo_ids(existing)}
    hashed_pw = get_password_hash(password)
    user_dict = {
        "email": email,
        "password": hashed_pw,
        "name": name,
        "phone": phone,
        "department": department,
        "year": year,
        "role": role,
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
        "photo": ""
    }
    result = await users_collection.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return {"msg": "Demo user created", "user": fix_mongo_ids(user_dict)}

# Endpoint to fetch activity logs for a user
@app.get("/api/activitylog")
async def get_activity_log(user=Depends(get_current_user)):
    logs = []
    async for log in activitylog_collection.find({"user": user["email"]}).sort("timestamp", -1):
        logs.append(fix_mongo_ids(log))
    return logs

# Mount static files only for non-API routes
@app.get("/{full_path:path}")
async def serve_static_files(full_path: str):
    # Don't serve static files for API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve static files from the build directory
    file_path = os.path.join(build_path, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Serve index.html for SPA routing
    index_path = os.path.join(build_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 