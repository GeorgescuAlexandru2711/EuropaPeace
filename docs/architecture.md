# Europa Peace System Architecture

This document presents the internal architecture of the Europa Peace System.

## Component Diagram

```mermaid
graph TD
    subgraph Client [Client Side]
        UI[User Interface - HTML/CSS/JS]
        Map[Leaflet Map Component]
        SocketJS[Socket.IO Client]
        HTTPClient[Fetch API]
    end

    subgraph Server [Flask Server]
        API[REST API Endpoints]
        Sockets[WebSocket Handlers - Socket.IO]
        Core[Business Logic & Auth]
        DBClient[MongoDB Client / MongoMock]
    end

    subgraph Database [Database Layer]
        MongoDB[(MongoDB Database)]
    end

    UI --> HTTPClient
    Map --> HTTPClient
    UI --> SocketJS
    
    HTTPClient -->|HTTP GET/POST/PUT| API
    SocketJS <-->|WebSockets| Sockets
    
    API --> Core
    Sockets --> Core
    Core --> DBClient
    
    DBClient -->|Read/Write| MongoDB
```

## Description

- **Client Side**: Uses plain HTML/CSS/JS, incorporating the Leaflet library for dynamic maps. It communicates with the backend via Fetch API for standard REST requests, and Socket.IO for real-time bidirectional communication (diplomatic chats, etc.).
- **Flask Server**: Acts as the backend serving the `index.html` file and offering an API. Uses `flask-socketio` to manage active WebSocket sessions. The `mongomock` fallback allows it to work out of the box in memory even if MongoDB is not installed.
- **Database Layer**: MongoDB holds persistent collections such as `countries`, `users`, `independence_requests`, `audiences`, and `reports`.
