# SketchGallery
Asynchronous Scalable Sketch-to-Image Generation Service

## Title and Participants
- Title: Sketch-to-Gallery(A Scalable Sketch-to-Image Generation Service)
- Participants: Sungboo Park and Dukhwan Kim

## Project Goals
- The goal of this project is to build a scalable web service that transforms simple sketches into high-quality rendered images. Through a REST API, users can upload rough sketches representing their initial ideas, and the system processes them with a generative model to create visual outputs.
- The architecture separates user interaction, processing, and storage into independent components, making the system scalable, modular, and well-suited for background workloads. Generated results are stored in a persistent gallery where users can later retrieve, browse, and manage their creations.
- More importantly, this service is designed around the idea of effortless creativity. A user only needs to provide a rough sketch, and the system can continue working in the background while the user is away, refining the input into an image that feels expressive, complete, and worthy of being displayed in a gallery.
- By lowering the barrier from imagination to creation, the project enables anyone to turn simple visual ideas into a growing personal collection of artwork. Ultimately, this project demonstrates how cloud-based service architecture can power scalable and modular AI-driven creative experiences.

## Software and Hardware Components

- Software Components
	1.	Ingress / Load Balancer : Routes external traffic to the REST API
	2.	REST API (Flask) : Handles user requests, uploads sketches, checks job status, and serves gallery metadata
	3.	Authentication Service : Manages user identity and access control
	4.	Metadata Database (Cloud SQL / Firestore) : Stores users, job status, gallery metadata, and model version info
	5.	Redis Streams : Message queue for asynchronous task processing and retry handling
	6.	Worker Service : Processes sketches using a generative model and writes results back to storage
	7.	Google Cloud Storage (Object Storage) : Stores input sketches, intermediate assets, and generated images
	8.	Gallery Service / Retrieval Layer : Allows users to browse, retrieve, and manage their generated artworks
	9.	Monitoring & Logging Stack : Collects logs, metrics, and health signals for reliability

- Hardware / Cloud Infrastructure
	1.	Google Cloud Platform (GCP)
	2.	Google Kubernetes Engine (GKE)
	3.	Compute Engine Node Pools for API and worker workloads


## Architecture Diagram
![Architecture Diagram](images/architecture.drawio.png)


## Interaction Between Components

1.	The user requests a sketch upload through the REST API.
2.	The REST API issues a signed upload URL and creates a job entry.
3.	The user uploads the sketch directly to Google Cloud Storage.
4.	The REST API enqueues a generation job in Redis after the upload is confirmed.
5.	A Worker pulls the job from Redis and downloads the sketch from Google Cloud Storage.
6.	The Worker generates a refined image using a generative model.
7.	The output image is stored in Google Cloud Storage.
8.	The Worker updates the job status, and the user retrieves the result through REST endpoints.
* This design ensures loose coupling between components and supports asynchronous processing.

## Debugging and Testing Strategy

- We will use multiple debugging strategies:
  1. kubectl logs to inspect logs from REST and Worker pods
  2.  Google Cloud Storage bucket inspection to verify input/output files
  3.  Port-forwarding for local debugging
- Testing approach:
  1. Unit testing REST endpoints
  2. Integration testing of full pipeline (upload → process → retrieve)
  3. Use of small sample inputs for fast iteration

## Use of Cloud Technologies - required
1. Kubernetes (GKE) – orchestration and scaling
2. Redis – distributed message queue
3. Google Cloud Storage / Object Storage – persistent storage (image data)
4. Databases - persistent storage (meta data)
5. Docker – containerization
6. Ingress / Load Balancer – external access

## Why This Project is Compelling
- This project is compelling because it combines AI-based image generation with a scalable asynchronous cloud architecture.
- It goes beyond a simple model demo by building a production-style service with decoupled APIs, Redis-based job processing, and persistent cloud storage.
- It is also user-centered, allowing simple sketches to be transformed into polished images for a personal gallery.

## Scope and Ambition
We believe this project is well within scope for the class and is appropriately ambitious. It is not too conservative, because it goes beyond building a simple web application and instead requires the design of a distributed, cloud-based system with asynchronous processing, decoupled services, persistent storage, and scalable workers. The project directly demonstrates important systems concepts such as loose coupling, fault isolation, job scheduling, storage separation, and scalability under concurrent requests. In that sense, it offers meaningful technical depth and reflects a realistic modern AI service architecture rather than a small standalone prototype.

At the same time, we do not believe the project is unrealistically ambitious. We intentionally bound the scope by using an existing generative model rather than training a large model from scratch, which allows us to focus on the core learning goals of the course: system design, implementation, and evaluation. In addition, the project can be developed in clear stages. A minimal version consists of sketch upload, autoscaling, background job processing, and result retrieval; more advanced features such as richer gallery functions, or extended performance testing can be added as stretch goals. This staged plan makes the project feasible while still leaving room for substantial technical contribution. For these reasons, we believe the project is neither too ambitious nor too conservative, but instead strikes a strong balance between practicality, depth, and educational value.




