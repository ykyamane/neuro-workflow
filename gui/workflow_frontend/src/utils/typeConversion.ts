// Determine if a string contains only digits
export const isNumeric = (str: string): boolean => {
  return /^\d+$/.test(str);
};

// Converting numbers to floats (as strings with decimal points)
export const convertToStrIncFloat = (value: any): any => {
  if (Array.isArray(value)) {
    // For arrays, recursively process each element
    return value.map(v => convertToStrIncFloat(v));
  } else if (value !== null && typeof value === "object") {
    // For objects, recursively process each property
    const result: Record<string, any> = {};
    for (const [key, val] of Object.entries(value)) {
      result[key] = convertToStrIncFloat(val);
    }
    return result;
  } else if (typeof value === "number") {
    // Numbers are always converted to strings with decimal points
    // Example: 1 → "1.0", 0.25 → "0.25"
    return value % 1 === 0 ? value.toFixed(1) : value.toString();
  } else {
    if (typeof value === "string") {
      if (isNumeric(value)){
        const valueF = parseFloat(value);
        return valueF % 1 === 0 ? valueF.toFixed(1) : valueF.toString();
      }
    }
    // Others (string, null, boolean, etc.) remain as is
    return value;
  }
};
