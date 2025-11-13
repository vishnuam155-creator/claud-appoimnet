# Medical Appointment System - React Frontend

Modern React-based frontend for the Medical Appointment Management System with Material-UI design.

## Features

- **Responsive Design** - Works seamlessly on desktop, tablet, and mobile devices
- **Material-UI Components** - Beautiful, accessible UI components
- **Multi-step Booking Flow** - Intuitive appointment booking process
- **Real-time Availability** - Check doctor availability in real-time
- **Patient Portal** - View and manage appointments
- **Admin Dashboard** - System statistics and management
- **React Query** - Efficient data fetching and caching
- **React Router** - Client-side routing

## Technology Stack

- **React 19** - UI framework
- **Material-UI (MUI)** - Component library
- **React Router** - Routing
- **TanStack Query (React Query)** - Data fetching and state management
- **Axios** - HTTP client
- **date-fns** - Date utilities

## Installation

### Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

### Setup

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Configure API URL (optional):**

Create a `.env` file in the frontend directory:
```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

3. **Start development server:**
```bash
npm start
```

The app will open at `http://localhost:3000`

## Available Scripts

### `npm start`
Runs the app in development mode at http://localhost:3000

### `npm test`
Launches the test runner in interactive watch mode

### `npm run build`
Builds the app for production to the `build` folder

## Pages

### 1. Home Page (`/`)
Landing page with system overview and quick access to booking

### 2. Book Appointment (`/book`)
Multi-step booking flow with 6 steps

### 3. Doctor List (`/doctors`)
Browse and filter doctors by specialization

### 4. My Appointments (`/my-appointments`)
Search and manage appointments by phone number

### 5. Admin Dashboard (`/admin`)
System statistics and management interface

## API Services

All API calls are centralized in the `services/` directory:
- `doctorService.js` - Doctor-related API calls
- `appointmentService.js` - Appointment-related API calls

## Deployment

### Build for Production

```bash
npm run build
```

The production build will be in the `build/` folder.

## Environment Variables

Create `.env` file:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
