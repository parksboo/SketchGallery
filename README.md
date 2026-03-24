# SketchGallery
A Scalable Sketch-to-Image Generation Service

## Title and Participants
- Title: Sketch-to-Gallery(A Scalable Sketch-to-Image Generation Service)
- Participants: Sungboo Park and Dukhwan Kim

## Project Goals
- The goal of this project is to build a scalable web service that transforms simple sketches into high-quality rendered images. Through a REST API, users can upload rough sketches representing their initial ideas, and the system processes them with a generative model to create visual outputs.
- The architecture separates user interaction, processing, and storage into independent components, making the system scalable, modular, and well-suited for background workloads. Generated results are stored in a persistent gallery where users can later retrieve, browse, and manage their creations.
- More importantly, this service is designed around the idea of effortless creativity. A user only needs to provide a rough sketch, and the system can continue working in the background while the user is away, refining the input into an image that feels expressive, complete, and worthy of being displayed in a gallery.
- By lowering the barrier from imagination to creation, the project enables anyone to turn simple visual ideas into a growing personal collection of artwork. Ultimately, this project demonstrates how cloud-based service architecture can power scalable and modular AI-driven creative experiences.

## Development Components


## Architecture Diagram
<img width="510" height="395" alt="image" src="https://github.com/user-attachments/assets/faa72b62-3415-4901-b2e6-f08c93be241e" />

## Interaction Between Components

1. The user uploads a sketch through the REST API.
2. The REST API stores the sketch in MinIO (input bucket).
3. The REST API sends a job request to Redis.
4. The Worker retrieves the job from Redis.
5. The Worker downloads the sketch from MinIO.
6. The Worker processes the sketch using a generative model.
7. The generated image is stored in MinIO (output bucket).
8. The user retrieves results via REST endpoints.
* This design ensures loose coupling between components and supports asynchronous processing.

## Debugging and Testing Strategy

- We will use multiple debugging strategies:
  1. kubectl logs to inspect logs from REST and Worker pods
  2.  Redis queue inspection (LRANGE) to verify job flow
  3.  MinIO bucket inspection to verify input/output files
  4.  Port-forwarding for local debugging
  5.  Logging system (Redis logging channel)
- Testing approach:
  1. Unit testing REST endpoints
  2. Integration testing of full pipeline (upload → process → retrieve)
  3. Use of small sample inputs for fast iteration
  4. Load testing by sending multiple requests
## Use of Cloud Technologies
1. Kubernetes (GKE) – orchestration and scaling
2. Redis – distributed message queue
3. MinIO / Object Storage – persistent storage
4. Docker – containerization
5. Ingress / Load Balancer – external access

## Why This Project is Compelling
- This project is interesting because it combines:
  1. AI-based image generation
  2. Scalable cloud architecture
- Unlike a simple lab extension, this project demonstrates how machine learning systems can be deployed in a production-style environment.
- Additionally, the idea of transforming simple sketches into fully rendered images provides a creative and engaging user experience.

## Scope and Ambition
- This project is ambitious but still within scope.
  1. It refer to the Lab 7 architecture (REST + Redis + Worker + Storage)
  2. The extension is replacing audio processing with image generation
  3. The system remains modular and manageable
- Potential risks:
  1. Model complexity (we will start with a simple model or API if needed)
  2. Resource usage (we will use small models or limited scaling initially)
- Overall, the project is achievable within the course timeline.




