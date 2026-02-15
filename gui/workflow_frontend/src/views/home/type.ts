import { Node, Edge } from "@xyflow/react";

export interface InputField {
  type: string;
  description?: string;
  required?: boolean;
  default_value?: any;
  constraints?: any;
  optional?: boolean;
}

export interface OutputField {
  type: string;
  description?: string;
  optional?: boolean;
}

export interface ParameterField {
  type?: string;
  description?: string;
  default_value?: any;
  constraints?: {
    min?: number;
    max?: number;
    options?: any[];
    [key: string]: any;
  };
  optional?: boolean;
  widget_type?: string;
  // Optimization metadata
  optimizable?: boolean;
  optimization_range?: [number, number] | number[];
  is_objective?: boolean;
  objective_range?: [number, number] | number[];
}

export interface Method {
  description?: string;
  inputs: string[];
  outputs: string[];
}

export interface SchemaFields {
  inputs: {
    [key: string]: InputField;
  };
  outputs: {
    [key: string]: OutputField;
  };
  parameters: {
    [key: string]: ParameterField;
  };
  methods: {
    [key: string]: Method;
  };
}

export interface CalculationNodeData {
  file_name: string;
  label: string;
  instanceName: string,
  schema: SchemaFields;
  nodeType?: string;
  operation?: string;
  // Node-specific parameter values ​​(overrides the default_value in the schema)
  nodeParameters?: {
    [key: string]: any;
  };
  isParamExpand?: boolean;
  color: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  workflow_context?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface FlowData {
  nodes: Node[];
  edges: Edge[];
}
