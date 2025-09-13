#!/bin/bash

# Start backend server
echo "Starting backend server..."
cd backend
npm install
npm start &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend development server
echo "Starting frontend development server..."
cd ../src
npm install
npm start &
FRONTEND_PID=$!

# Function to cleanup processes on exit
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit
}

# Trap Ctrl+C and call cleanup
trap cleanup INT

# Wait for both processes
wait
