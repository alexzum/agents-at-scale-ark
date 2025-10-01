#!/usr/bin/env node
/**
 * Automatically sync CRD schemas to resource documentation
 * 
 * This script extracts schema information from CRDs and updates the
 * corresponding documentation files, ensuring they stay in sync with code changes.
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
        case 'Model': resourceKey = 'models'; break;
        case 'Tool': resourceKey = 'tools'; break;
        case 'Agent': resourceKey = 'agent'; break;
        case 'MCPServer': resourceKey = 'mcpserver'; break;
        case 'Memory': resourceKey = 'memory'; break;
        default: resourceKey = kind.toLowerCase();
      }
      
      crds[resourceKey] = crdData;
    } catch (error) {
      console.error(`Error loading CRD ${filePath}:`, error.message);
    }
  }
  
  return crds;
}

function generateDefaultValue(fieldSchema, fieldName) {
  if (fieldSchema.default !== undefined) {
    return fieldSchema.default;
  }
  
  switch (fieldSchema.type) {
    case 'string':
      if (fieldSchema.enum) return fieldSchema.enum[0];
      
      // Context-aware defaults
      switch (fieldName.toLowerCase()) {
        case 'prompt': return 'You are a helpful assistant';
        case 'name': return 'example-name';
        case 'address': return 'http://example.com:8080';
        case 'url': return 'https://api.example.com/endpoint';
        case 'description': return 'Example description';
        case 'model': return 'gpt-4o-mini';
        case 'type': return fieldSchema.enum ? fieldSchema.enum[0] : 'http';
        case 'method': return 'GET';
        case 'namespace': return 'default';
        case 'toolname': return 'example_tool';
        default: return 'example-value';
      }
      
    case 'integer': 
    case 'number':
      return fieldSchema.minimum !== undefined ? fieldSchema.minimum : 
             fieldSchema.maximum !== undefined ? Math.min(fieldSchema.maximum, 10) : 30;
      
    case 'boolean':
      return fieldSchema.default !== undefined ? fieldSchema.default : true;
      
    case 'object':
      if (fieldSchema.properties) {
        return generateSpecFromSchema(fieldSchema);
      }
      return {};
      
    case 'array':
      if (fieldSchema.items) {
        return [generateDefaultValue(fieldSchema.items, `${fieldName}Item`)];
      }
      return [];
      
    default:
      return null;
  }
}

function generateSpecFromSchema(schema) {
  if (!schema || !schema.properties) return {};
  
  const spec = {};
  
  // Add required fields first
  if (schema.required) {
    for (const field of schema.required) {
      const fieldSchema = schema.properties[field];
      if (fieldSchema) {
        spec[field] = generateDefaultValue(fieldSchema, field);
      }
    }
  }
  
  // Add some optional fields for better examples (max 2-3 to keep examples concise)
  const optionalFields = Object.keys(schema.properties).filter(field => 
    !schema.required?.includes(field)
  ).slice(0, 2);
  
  for (const field of optionalFields) {
    const fieldSchema = schema.properties[field];
    // Only add optional fields that are commonly used
    if (fieldSchema && shouldIncludeOptionalField(field, fieldSchema)) {
      spec[field] = generateDefaultValue(fieldSchema, field);
    }
  }
  
  return spec;
}

function shouldIncludeOptionalField(fieldName, fieldSchema) {
  // Include commonly used optional fields in examples
  const commonFields = ['description', 'namespace', 'timeout', 'headers', 'modelRef'];
  return commonFields.includes(fieldName) || 
         fieldSchema.description?.toLowerCase().includes('example') ||
         fieldSchema.type === 'string' && fieldName.length < 15; // Short field names are usually important
}

function generateValidYamlExample(crd, exampleName = 'example') {
  const schema = crd.spec.versions[0].schema.openAPIV3Schema.properties.spec;
  const isNamespaced = crd.spec.scope === 'Namespaced';
  
  const example = {
    apiVersion: `${crd.spec.group}/${crd.spec.versions[0].name}`,
    kind: crd.spec.names.kind,
    metadata: {
      name: `${exampleName}-${crd.spec.names.kind.toLowerCase()}`,
      ...(isNamespaced && { namespace: 'default' })
    },
    spec: generateSpecFromSchema(schema)
  };
  
  return yaml.dump(example, { 
    indent: 2,
    lineWidth: 120,
    noRefs: true,
    sortKeys: false
  }).trim();
}

function hasEducationalContent(yamlContent) {
  // Don't replace examples that have educational value:
  // - Comments explaining fields
  // - Realistic example values
  // - Multi-line content like prompts
  const hasComments = yamlContent.includes('#');
  const hasMultilineContent = yamlContent.includes('|') || yamlContent.includes('>');
  const hasRealisticNames = !/example-.*-.*/.test(yamlContent); // Not generic generated names
  const hasRichContent = yamlContent.length > 200; // Substantial examples
  
  return hasComments || hasMultilineContent || (hasRealisticNames && hasRichContent);
}

function updateYamlExamples(content, crd, resourceName) {
  const targetKind = crd.spec.names.kind;
  const yamlBlockRegex = /```yaml\n([\s\S]*?)\n```/g;
  let exampleCount = 0;
  let preservedCount = 0;
  let replacedCount = 0;
  
  const result = content.replace(yamlBlockRegex, (match, yamlContent) => {
    try {
      // Only process YAML blocks for this resource kind
      if (yamlContent.includes(`kind: ${targetKind}`) && 
          yamlContent.includes('apiVersion: ark.mckinsey.com')) {
        
        exampleCount++;
        
        // PRESERVE educational content - don't replace good examples!
        if (hasEducationalContent(yamlContent)) {
          preservedCount++;
          return match; // Keep the original
        }
        
        // Only replace if it's clearly a minimal/broken example
        if (yamlContent.trim().split('\n').length <= 8 && !yamlContent.includes('#')) {
          const nameMatch = yamlContent.match(/name:\s*([^\s\n]+)/);
          const exampleName = nameMatch ? nameMatch[1] : 'example';
          
          const newYaml = generateValidYamlExample(crd, exampleName);
          replacedCount++;
          return `\`\`\`yaml\n${newYaml}\n\`\`\``;
        } else {
          preservedCount++;
        }
      }
    } catch (error) {
      console.warn(`      ⚠️ Error processing YAML example: ${error.message}`);
    }
    
    return match;
  });
  
  // Summary of actions taken
  if (exampleCount > 0) {
    console.log(`      📊 Processed ${exampleCount} ${targetKind} example(s): ${preservedCount} preserved, ${replacedCount} auto-generated`);
  }
  
  return result;
}

function updateResourceDoc(resourceName, crd) {
  const docPath = path.join(RESOURCES_DOCS_PATH, `${resourceName}.mdx`);
  
  if (!fs.existsSync(docPath)) {
    console.log(`   ⚠️ No documentation file found for ${resourceName}, skipping`);
    return;
  }
  
  console.log(`📝 Updating schema info for ${resourceName}`);
  
  const currentContent = fs.readFileSync(docPath, 'utf8');
  const schema = crd.spec.versions[0].schema.openAPIV3Schema;
  const specSchema = schema.properties?.spec;
  
  if (!specSchema) {
    console.log(`   ⚠️ No spec schema found for ${resourceName}`);
    return;
  }
  
  // Update resource metadata (API versions, kinds, scopes)
  let updatedContent = updateResourceInfo(currentContent, crd);
  
  // Smart YAML example updates (preserve educational content)
  updatedContent = updateYamlExamples(updatedContent, crd, resourceName);
  
  fs.writeFileSync(docPath, updatedContent);
  console.log(`   ✅ Updated ${resourceName}.mdx`);
}

function updateResourceInfo(content, crd) {
  const group = crd.spec.group;
  const version = crd.spec.versions[0].name;
  const kind = crd.spec.names.kind;
  const plural = crd.spec.names.plural;
  const scope = crd.spec.scope;
  
  // Only update existing Resource Information section if it exists
  const resourceInfoRegex = /## Resource Information[\s\S]*?(?=\n## |\n# |$)/;
  const newResourceInfo = `## Resource Information

- **API Version:** \`${group}/${version}\`
- **Kind:** \`${kind}\`
- **Plural:** \`${plural}\`
- **Scope:** \`${scope}\`

`;
  
  if (resourceInfoRegex.test(content)) {
    return content.replace(resourceInfoRegex, newResourceInfo);
  }

  return content;
}

function syncAllResources() {
  console.log('🔄 Syncing CRD schemas to documentation (Smart Mode)\n');

  const crds = loadCRDs();
  const resourceTypes = ['models', 'agent', 'mcpserver', 'memory', 'tools'];
  
  let updated = 0;
  
  for (const resource of resourceTypes) {
    const crd = crds[resource];
    if (crd) {
      updateResourceDoc(resource, crd);
      updated++;
    } else {
      console.log(`❌ ${resource}: CRD file not found in ark/config/crd/bases/`);
    }
    console.log(); // Empty line
  }
  
  console.log('📋 Synchronization Summary:');
  console.log(`   ✅ ${updated}/${resourceTypes.length} resource files processed`);
  
  if (updated === resourceTypes.length) {
    console.log('\n🎉 All documentation is now synchronized with CRD schemas!');
  } else {
    console.log('\n⚠️ Some resources could not be synchronized - check CRD files exist');
  }
  
  return updated > 0;
}

// Check dependencies
try {
  require('js-yaml');
} catch (error) {
  console.error('Error: js-yaml is not installed. Please run: npm install js-yaml');
  process.exit(1);
}

if (require.main === module) {
  syncAllResources();
}

module.exports = { syncAllResources, loadCRDs };
