import React from 'react';
import { Container, Accordion, Card } from 'react-bootstrap';

const ApiDocs = () => {
  const endpoints = [
    {
      title: 'User Authentication',
      endpoints: [
        {
          method: 'POST',
          path: '/api/auth/register',
          description: 'Register a new user account',
          parameters: [
            { name: 'name', type: 'string', required: true, description: 'User full name' },
            { name: 'email', type: 'string', required: true, description: 'User email address' },
            { name: 'password', type: 'string', required: true, description: 'User password (min 8 characters)' }
          ]
        },
        {
          method: 'POST',
          path: '/api/auth/login',
          description: 'Authenticate user and get access token',
          parameters: [
            { name: 'email', type: 'string', required: true },
            { name: 'password', type: 'string', required: true }
          ]
        }
      ]
    },
    {
      title: 'Water Analysis',
      endpoints: [
        {
          method: 'GET',
          path: '/api/analysis/detect',
          description: 'Detect current algae in a location',
          parameters: [
            { name: 'lat', type: 'float', required: true, description: 'Latitude coordinate' },
            { name: 'lon', type: 'float', required: true, description: 'Longitude coordinate' }
          ]
        },
        {
          method: 'GET',
          path: '/api/analysis/predict',
          description: 'Predict future algae spread in a location',
          parameters: [
            { name: 'lat', type: 'float', required: true },
            { name: 'lon', type: 'float', required: true }
          ]
        }
      ]
    },
    {
      title: 'Analysis History',
      endpoints: [
        {
          method: 'GET',
          path: '/api/analysis/history',
          description: 'Get user analysis history',
          parameters: [
            { name: 'page', type: 'int', required: false, description: 'Page number (default: 1)' },
            { name: 'per_page', type: 'int', required: false, description: 'Items per page (default: 10)' }
          ]
        }
      ]
    }
  ];

  return (
    <Container className="py-4">
      <div className="text-center mb-5">
        <h1>AquaVision AI API Documentation</h1>
        <p className="lead">
          Technical documentation for interacting with the AquaVision AI REST API
        </p>
      </div>

      <div className="mb-5">
        <h2 className="mb-4">Getting Started</h2>
        <p>
          The AquaVision API provides programmatic access to water quality analysis features. 
          All API endpoints require authentication using a JSON Web Token (JWT).
        </p>
        
        <h4 className="mt-4">Authentication</h4>
        <p>
          To authenticate, include the JWT token in the Authorization header:
        </p>
        <pre className="bg-dark text-light p-3 rounded">
          {`Authorization: Bearer <your_api_key>`}
        </pre>
      </div>

      <h2 className="mb-4">API Endpoints</h2>
      <Accordion defaultActiveKey="0">
        {endpoints.map((section, sectionIndex) => (
          <Accordion.Item eventKey={sectionIndex.toString()} key={sectionIndex}>
            <Accordion.Header>{section.title}</Accordion.Header>
            <Accordion.Body>
              {section.endpoints.map((endpoint, endpointIndex) => (
                <Card key={endpointIndex} className="mb-4">
                  <Card.Header className="d-flex justify-content-between align-items-center">
                    <span className="badge bg-primary me-2">{endpoint.method}</span>
                    <code>{endpoint.path}</code>
                  </Card.Header>
                  <Card.Body>
                    <Card.Title>{endpoint.description}</Card.Title>
                    
                    {endpoint.parameters && endpoint.parameters.length > 0 && (
                      <>
                        <h6>Parameters:</h6>
                        <table className="table table-sm">
                          <thead>
                            <tr>
                              <th>Name</th>
                              <th>Type</th>
                              <th>Required</th>
                              <th>Description</th>
                            </tr>
                          </thead>
                          <tbody>
                            {endpoint.parameters.map((param, paramIndex) => (
                              <tr key={paramIndex}>
                                <td><code>{param.name}</code></td>
                                <td>{param.type}</td>
                                <td>{param.required ? 'Yes' : 'No'}</td>
                                <td>{param.description}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </>
                    )}
                    
                    <h6 className="mt-3">Example Request:</h6>
                    <pre className="bg-dark text-light p-3 rounded">
                      {`curl -X ${endpoint.method} \\\n`}
                      {`  '${endpoint.path}?${endpoint.parameters?.map(p => `${p.name}=<value>`).join('&')}' \\\n`}
                      {`  -H 'Authorization: Bearer <your_api_key>'`}
                    </pre>
                    
                    <h6>Example Response:</h6>
                    <pre className="bg-dark text-light p-3 rounded">
                      {`{\n`}
                      {`  "success": true,\n`}
                      {`  "data": {\n`}
                      {`    "image_url": "/static/analysis/result_12345.png",\n`}
                      {`    "coverage": 25.7,\n`}
                      {`    "severity": "medium",\n`}
                      {`    "bounds": [[12.34, 56.78], [12.35, 56.79]]\n`}
                      {`  }\n`}
                      {`}`}
                    </pre>
                  </Card.Body>
                </Card>
              ))}
            </Accordion.Body>
          </Accordion.Item>
        ))}
      </Accordion>
    </Container>
  );
};

export default ApiDocs;