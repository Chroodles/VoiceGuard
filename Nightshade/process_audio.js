const { parseMultipartFormData, getUploadStream } = require('@netlify/functions');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

exports.handler = async (event) => {
  try {
    const { files } = await parseMultipartFormData(event);
    const audioFile = files.audio[0];
    
    // Save the file locally
    const tempPath = path.join('/tmp', audioFile.name);
    fs.writeFileSync(tempPath, audioFile.content);
    
    // Process the audio file
    // (Replace this with your actual audio processing logic)
    await new Promise((resolve, reject) => {
      exec(`python3 process_audio.py ${tempPath}`, (error, stdout, stderr) => {
        if (error) {
          reject(`Error: ${stderr}`);
        } else {
          resolve(stdout);
        }
      });
    });

    // Return the processed file as a response
    const processedFilePath = tempPath.replace('.mp3', '_processed.mp3');
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'audio/mpeg' },
      body: fs.readFileSync(processedFilePath).toString('base64'),
      isBase64Encoded: true
    };
  } catch (error) {
    return {
      statusCode: 500,
      body: `Error: ${error.message}`
    };
  }
};
