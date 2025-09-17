import React, { useState } from "react";
import { Upload, Camera, CheckCircle, XCircle } from "lucide-react";

const TestPhotoUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string>("");
  const [irisResponse, setIrisResponse] = useState<any>(null);
  
  // Use the test user we just created
  const TEST_USER_ID = "e96b4389-3996-4b59-8c10-698c24930098";

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !previewUrl) return;

    setUploadStatus("Uploading to IRIS...");
    
    try {
      // Send to IRIS API
      const response = await fetch("/api/iris/unified-chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: TEST_USER_ID,
          session_id: `test-session-${Date.now()}`,
          message: "I want to upload this photo for my home project",
          image: previewUrl.split(",")[1], // Remove data:image/jpeg;base64, prefix
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setIrisResponse(data);
      setUploadStatus("Upload successful! IRIS is analyzing your photo.");
      
      // Check if image was saved to database
      const checkResponse = await fetch(`/api/iris/images?user_id=${TEST_USER_ID}`);
      if (checkResponse.ok) {
        const images = await checkResponse.json();
        console.log("Images saved to database:", images);
      }
    } catch (error) {
      console.error("Upload error:", error);
      setUploadStatus(`Upload failed: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Test Photo Upload for Your House</h1>
        
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">📸 Upload a Photo from Your House</h2>
          <p className="text-gray-600 mb-4">
            Take a photo of any room or area in your house and upload it here to test the IRIS system.
            This will verify that photos are properly saved and processed.
          </p>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            {previewUrl ? (
              <div className="space-y-4">
                <img 
                  src={previewUrl} 
                  alt="Preview" 
                  className="max-w-full max-h-96 mx-auto rounded-lg"
                />
                <p className="text-sm text-gray-600">
                  Selected: {selectedFile?.name}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <Camera className="w-16 h-16 mx-auto text-gray-400" />
                <p className="text-gray-600">
                  Click to select a photo from your house
                </p>
              </div>
            )}
            
            <input
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
              id="photo-upload"
            />
            <label
              htmlFor="photo-upload"
              className="inline-block mt-4 px-6 py-3 bg-blue-600 text-white rounded-lg cursor-pointer hover:bg-blue-700"
            >
              <Upload className="inline-block w-5 h-5 mr-2" />
              Choose Photo
            </label>
          </div>
          
          {selectedFile && (
            <button
              onClick={handleUpload}
              className="mt-6 w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold"
            >
              Upload to IRIS
            </button>
          )}
        </div>
        
        {uploadStatus && (
          <div className={`bg-white rounded-lg shadow-lg p-6 mb-6 ${
            uploadStatus.includes("failed") ? "border-l-4 border-red-500" : 
            uploadStatus.includes("successful") ? "border-l-4 border-green-500" : 
            "border-l-4 border-blue-500"
          }`}>
            <h3 className="text-lg font-semibold mb-2 flex items-center">
              {uploadStatus.includes("failed") ? (
                <XCircle className="w-5 h-5 mr-2 text-red-500" />
              ) : uploadStatus.includes("successful") ? (
                <CheckCircle className="w-5 h-5 mr-2 text-green-500" />
              ) : (
                <div className="w-5 h-5 mr-2 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              )}
              Status
            </h3>
            <p>{uploadStatus}</p>
          </div>
        )}
        
        {irisResponse && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-4">IRIS Response</h3>
            <div className="bg-gray-50 rounded p-4">
              <p className="text-gray-800">{irisResponse.response}</p>
              {irisResponse.workflow_questions && (
                <div className="mt-4">
                  <h4 className="font-semibold mb-2">Follow-up Questions:</h4>
                  <ul className="list-disc list-inside space-y-1">
                    {irisResponse.workflow_questions.map((q: string, i: number) => (
                      <li key={i} className="text-gray-700">{q}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
        
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-2">Test User Information</h3>
          <p className="text-sm text-gray-600">User ID: {TEST_USER_ID}</p>
          <p className="text-sm text-gray-600">Email: testhome@example.com</p>
          <p className="text-sm text-gray-600">Name: Test Homeowner</p>
        </div>
      </div>
    </div>
  );
};

export default TestPhotoUpload;