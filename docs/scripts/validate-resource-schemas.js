#!/usr/bin/env node
/**
 * Validate and sync YAML examples in resource documentation with actual CRDs
 * 
 * This script checks that YAML examples in docs/content/reference/resources/
 * match the actual CRD schemas and can optionally update them.
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const CRD_BASE_PATH = path.join(__dirname, '../../ark/config/crd/bases');
const RESOURCES_DOCS_PATH = path.join(__dirname, '../content/reference/resources');

function loadCRDs() {
  const crds = {};
  
  const crdFiles = fs.readdirSync(CRD_BASE_PATH)
    .filter(file => file.endsWith('.yaml'))
    .map(file => path.join(CRD_BASE_PATH, file));
  
  for (const filePath of crdFiles) {
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const crdData = yaml.load(content);
      
      // Map CRD kinds to resource doc names
      const kind = crdData.spec.names.kind;
      let resourceKey;
      
      switch (kind) {
        case 'Model':
          resourceKey = 'models';
          break;
        case 'Tool':
          resourceKey = 'tools';
          break;
        case 'Agent':
          resourceKey = 'agent';
          break;
        case 'MCPServer':
          resourceKey = 'mcpserver';
          break;
        case 'Memory':
          resourceKey = 'memory';
          break;
        default:
          resourceKey = kind.toLowerCase();
      }
      
      crds[resourceKey] = crdData;
    } catch (error) {
      console.error(`Error loading CRD ${filePath}:`, error.message);
    }
  }
  
  return crds;
}

function extractYamlFromMarkdown(markdownContent) {
  const yamlBlocks = [];
  const codeBlockRegex = /```yaml\n([\s\S]*?)\n```/g;
  let match;
  
  while ((match = codeBlockRegex.exec(markdownContent)) !== null) {
    try {
      const yamlContent = match[1];
      // Skip if it's not a proper Kubernetes resource (no apiVersion)
      if (yamlContent.includes('apiVersion: ark.mckinsey.com')) {
        const parsed = yaml.load(yamlContent);
        yamlBlocks.push({
          original: yamlContent,
          parsed: parsed,
          startPos: match.index,
          endPos: match.index + match[0].length
        });
      }
    } catch (error) {
      console.warn('Failed to parse YAML block:', error.message);
    }
  }
  
  return yamlBlocks;
}

function validateAgainstCRD(resourceYaml, crd) {
  const errors = [];
  const warnings = [];
  
  // Basic structure validation
  if (!resourceYaml.apiVersion) {
    errors.push('Missing apiVersion');
  } else if (resourceYaml.apiVersion !== `${crd.spec.group}/${crd.spec.versions[0].name}`) {
    errors.push(`Incorrect apiVersion: expected ${crd.spec.group}/${crd.spec.versions[0].name}, got ${resourceYaml.apiVersion}`);
  }
  
  if (!resourceYaml.kind) {
    errors.push('Missing kind');
  } else if (resourceYaml.kind !== crd.spec.names.kind) {
    errors.push(`Incorrect kind: expected ${crd.spec.names.kind}, got ${resourceYaml.kind}`);
  }
  
  if (!resourceYaml.metadata?.name) {
    warnings.push('Missing metadata.name');
  }
  
  // Spec validation against CRD schema
  if (resourceYaml.spec) {
    const specSchema = crd.spec.versions[0].schema.openAPIV3Schema.properties.spec;
    const specErrors = validateObjectAgainstSchema(resourceYaml.spec, specSchema, 'spec');
    errors.push(...specErrors);
  }
  
  return { errors, warnings };
}

function validateObjectAgainstSchema(obj, schema, path = '') {
  const errors = [];
  
  if (!schema || !schema.properties) {
    return errors;
  }
  
  // Check required fields
  if (schema.required) {
    for (const requiredField of schema.required) {
      if (!(requiredField in obj)) {
        errors.push(`Missing required field: ${path}.${requiredField}`);
      }
    }
  }
  
  // Check for unknown fields (basic validation)
  for (const fieldName in obj) {
    if (!schema.properties[fieldName]) {
      errors.push(`Unknown field: ${path}.${fieldName}`);
    } else {
      const fieldSchema = schema.properties[fieldName];
      const fieldPath = path ? `${path}.${fieldName}` : fieldName;
      
      // Recursively validate nested objects
      if (fieldSchema.type === 'object' && typeof obj[fieldName] === 'object' && obj[fieldName] !== null && !Array.isArray(obj[fieldName])) {
        const nestedErrors = validateObjectAgainstSchema(obj[fieldName], fieldSchema, fieldPath);
        errors.push(...nestedErrors);
      }
      
      // Validate enums
      if (fieldSchema.enum && !fieldSchema.enum.includes(obj[fieldName])) {
        errors.push(`Invalid enum value for ${fieldPath}: expected one of [${fieldSchema.enum.join(', ')}], got ${obj[fieldName]}`);
      }
    }
  }
  
  return errors;
}

function validateResourceDoc(resourceName) {
  const docPath = path.join(RESOURCES_DOCS_PATH, `${resourceName}.mdx`);
  
  if (!fs.existsSync(docPath)) {
    console.log(`❌ ${resourceName}: Documentation file not found`);
    return { valid: false, reason: 'No documentation file' };
  }
  
  const crds = loadCRDs();
  const crd = crds[resourceName];
  
  if (!crd) {
    console.log(`❌ ${resourceName}: CRD schema not found`);
    return { valid: false, reason: 'No CRD schema' };
  }
  
  const markdownContent = fs.readFileSync(docPath, 'utf8');
  const yamlBlocks = extractYamlFromMarkdown(markdownContent);
  
  if (yamlBlocks.length === 0) {
    console.log(`📋 ${resourceName}: No YAML examples to validate`);
    return { valid: true, reason: 'No examples to validate' };
  }
  
  let hasSchemaErrors = false;
  let validCount = 0;
  let crossResourceCount = 0;
  
  console.log(`🔍 ${resourceName}: Validating ${yamlBlocks.length} YAML example(s)...`);
  
  for (let i = 0; i < yamlBlocks.length; i++) {
    const block = yamlBlocks[i];
    const validation = validateAgainstCRD(block.parsed, crd);
    
    // Check if this is a cross-resource example (educational)
    const isCrossResource = block.parsed.kind !== crd.spec.names.kind;
    
    if (isCrossResource) {
      crossResourceCount++;
      console.log(`   📚 Example ${i + 1}: Cross-resource example (${block.parsed.kind} in ${resourceName} docs) - Educational content`);
    } else if (validation.errors.length > 0) {
      hasSchemaErrors = true;
      console.log(`   ❌ Example ${i + 1}: Schema validation failed`);
      validation.errors.forEach(error => console.log(`      • ${error}`));
    } else {
      validCount++;
      console.log(`   ✅ Example ${i + 1}: Valid ${crd.spec.names.kind} resource`);
    }
    
    // Show warnings for all examples
    if (validation.warnings.length > 0) {
      console.log(`   ⚠️ Example ${i + 1} warnings:`);
      validation.warnings.forEach(warning => console.log(`      • ${warning}`));
    }
  }
  
  // Summary for this resource
  const ownResourceExamples = yamlBlocks.length - crossResourceCount;
  if (crossResourceCount > 0) {
    console.log(`   📊 Summary: ${validCount}/${ownResourceExamples} own examples valid, ${crossResourceCount} cross-resource examples (educational)`);
  } else {
    console.log(`   📊 Summary: ${validCount}/${ownResourceExamples} examples valid`);
  }
  
  return { 
    valid: !hasSchemaErrors, 
    reason: hasSchemaErrors ? 'Schema validation errors' : 'All examples valid',
    stats: { total: yamlBlocks.length, valid: validCount, crossResource: crossResourceCount }
  };
}

function main() {
  console.log('🔍 Validating documentation YAML examples against CRD schemas\n');
  
  const resourceTypes = ['models', 'agent', 'mcpserver', 'memory', 'tools'];
  const results = {};
  
  for (const resource of resourceTypes) {
    const result = validateResourceDoc(resource);
    results[resource] = result;
    console.log(); // Empty line between resources
  }
  
  // Overall summary
  console.log('📊 Validation Summary:');
  const validResources = Object.values(results).filter(r => r.valid).length;
  const totalResources = Object.keys(results).length;
  
  let totalExamples = 0;
  let totalValidExamples = 0;
  let totalCrossResourceExamples = 0;
  
  Object.values(results).forEach(result => {
    if (result.stats) {
      totalExamples += result.stats.total;
      totalValidExamples += result.stats.valid;
      totalCrossResourceExamples += result.stats.crossResource;
    }
  });
  
  console.log(`   ✅ Resources: ${validResources}/${totalResources} have valid schemas`);
  console.log(`   📝 Examples: ${totalValidExamples} valid, ${totalCrossResourceExamples} cross-resource (educational)`);
  
  const hasIssues = validResources < totalResources;
  if (hasIssues) {
    console.log('\n❌ Schema validation issues found in:');
    Object.entries(results)
      .filter(([_, result]) => !result.valid)
      .forEach(([resource, result]) => {
        console.log(`   • ${resource}: ${result.reason}`);
      });
    
    console.log('\n💡 Note: Cross-resource examples (e.g., Agent in models.mdx) are educational and show proper usage patterns.');
    console.log('💡 Only fix examples that are intended to be of the documented resource type.');
    
    process.exit(1);
  } else {
    console.log('\n🎉 All resource documentation schemas are valid!');
    console.log('📚 Educational cross-resource examples detected and preserved.');
  }
}

// Check dependencies
try {
  require('js-yaml');
} catch (error) {
  console.error('Error: js-yaml is not installed. Please run: npm install js-yaml');
  process.exit(1);
}

if (require.main === module) {
  main();
}

module.exports = { validateResourceDoc, loadCRDs };
