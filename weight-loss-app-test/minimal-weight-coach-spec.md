# Weight Management System: Minimal Specification

## Overview
Build a simple web application that combines Claude's conversational abilities with a background obesity network model. The system will maintain natural conversation while using the computational model to inform recommendations.

## Tech Stack
- **Frontend**: Astro with TypeScript
- **Database**: AstroDB
- **LLM**: Claude API
- **Network Model**: Python backend with NetworkX

## Core Components

### 1. Minimalist Chat Interface
- Clean, simple chat UI
- Text-only interaction
- Minimal styling with focus on conversation

### 2. Claude Integration
- Connect to Claude API
- Use function calling to extract structured data
- Store conversation in AstroDB

### 3. Network Model
- Implement obesity factor network in Python
- Update network based on conversation data
- Generate recommendations based on network analysis

## Implementation

### Database Structure
```typescript
interface User {
  id: string;
  networkState: {
    factors: Record<string, number>;
    relationships: Array<{from: string, to: string, strength: number}>;
  };
  conversationHistory: Array<{
    timestamp: Date;
    message: string;
    response: string;
  }>;
}
```

### Claude Integration
- Pass conversation context and network-derived recommendations to Claude
- Extract structured data from conversations using function calling
- Update network model with extracted data

### Network Model
- Implement simple Bayesian updates for network parameters
- Calculate intervention potentials for modifiable factors
- Generate recommendations based on highest impact factors

## Development Steps
1. Implement basic chat UI with Astro
2. Connect to Claude API
3. Build simple network model in Python
4. Create data extraction system
5. Implement recommendation injection
