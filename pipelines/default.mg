{
  "header": {
    "pipelineVersion": "2.2",
    "releaseVersion": "2023.3.0",
    "fileVersion": "1.1",
    "template": true,
    "nodesVersions": {}
  },
  "graph": {
    "CameraInit_1": {
      "nodeType": "CameraInit",
      "position": [0, 0],
      "inputs": {}
    },
    "FeatureExtraction_1": {
      "nodeType": "FeatureExtraction",
      "position": [200, 0],
      "inputs": {
        "input": "{CameraInit_1.output}"
      }
    },
    "FeatureMatching_1": {
      "nodeType": "FeatureMatching",
      "position": [400, 0],
      "inputs": {
        "input": "{FeatureExtraction_1.input}",
        "featuresFolders": "{FeatureExtraction_1.output}"
      }
    },
    "StructureFromMotion_1": {
      "nodeType": "StructureFromMotion",
      "position": [600, 0],
      "inputs": {
        "input": "{FeatureMatching_1.input}",
        "featuresFolders": "{FeatureMatching_1.featuresFolders}",
        "matchesFolders": "{FeatureMatching_1.output}"
      }
    },
    "PrepareDenseScene_1": {
      "nodeType": "PrepareDenseScene",
      "position": [800, 0],
      "inputs": {
        "input": "{StructureFromMotion_1.output}"
      }
    },
    "DepthMap_1": {
      "nodeType": "DepthMap",
      "position": [1000, 0],
      "inputs": {
        "input": "{PrepareDenseScene_1.input}",
        "imagesFolder": "{PrepareDenseScene_1.output}"
      }
    },
    "DepthMapFilter_1": {
      "nodeType": "DepthMapFilter",
      "position": [1200, 0],
      "inputs": {
        "input": "{DepthMap_1.input}",
        "depthMapsFolder": "{DepthMap_1.output}"
      }
    },
    "Meshing_1": {
      "nodeType": "Meshing",
      "position": [1400, 0],
      "inputs": {
        "input": "{DepthMapFilter_1.input}",
        "depthMapsFolder": "{DepthMapFilter_1.depthMapsFolder}",
        "depthMapsFilterFolder": "{DepthMapFilter_1.output}"
      }
    },
    "MeshFiltering_1": {
      "nodeType": "MeshFiltering",
      "position": [1600, 0],
      "inputs": {
        "inputMesh": "{Meshing_1.outputMesh}"
      }
    },
    "Texturing_1": {
      "nodeType": "Texturing",
      "position": [1800, 0],
      "inputs": {
        "input": "{Meshing_1.input}",
        "imagesFolder": "{PrepareDenseScene_1.output}",
        "inputMesh": "{MeshFiltering_1.outputMesh}"
      }
    }
  }
}

