import React from 'react';

interface AddressInputSimpleProps {
  value: string;
  onChange: (address: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

const AddressInputSimple: React.FC<AddressInputSimpleProps> = ({
  value,
  onChange,
  placeholder = "Enter property address",
  className = "",
  disabled = false
}) => {
  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        className={`w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${className}`}
      />
      <div className="text-xs text-gray-500 mt-1">
        Enter your full property address
      </div>
    </div>
  );
};

export default AddressInputSimple;