Application-Aware Network Slice Manager developed for 5G-Int5Gent EU Project.

# Deployment
Build the image of the Application-Aware Network Slice Manager
```bash
docker build -t app-aware-nsm -f deployment/Dockerfile . 
```
or pull the image from this repository, then start the application:
```bash
docker run -p 5000:5000 app-aware-nsm
```