import React, { useState } from 'react';

interface AccordionItemProps {
  id: string;
  trigger: React.ReactNode;
  children: React.ReactNode;
  isOpen?: boolean;
  onToggle?: () => void;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  trigger,
  children,
  isOpen = false,
  onToggle
}) => {
  return (
    <div className={`border border-slate-200 rounded-xl overflow-hidden mb-3 transition-all duration-300 ${
      isOpen ? 'bg-slate-50/50 shadow-sm border-slate-300/80' : 'bg-white hover:border-slate-300'
    }`}>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between text-left font-bold text-slate-800 text-sm transition-all px-5 py-4 hover:text-slate-900 cursor-pointer"
      >
        <div className="flex-1 pr-4">{trigger}</div>
        <div className={`w-6 h-6 rounded-full bg-slate-100/80 hover:bg-slate-200 flex items-center justify-center transition-all duration-300 ${
          isOpen ? 'rotate-180 bg-navy-100 text-navy-800' : 'text-slate-500'
        }`}>
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-3.5 w-3.5"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </div>
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isOpen ? 'max-h-[1000px] opacity-100 border-t border-slate-200/60' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="text-xs text-slate-600 leading-relaxed font-sans px-5 py-4 bg-white/70">
          {children}
        </div>
      </div>
    </div>
  );
};

interface AccordionProps {
  children: React.ReactElement<AccordionItemProps> | React.ReactElement<AccordionItemProps>[];
  allowMultiple?: boolean;
}

export const Accordion: React.FC<AccordionProps> = ({ children, allowMultiple = false }) => {
  const [openIds, setOpenIds] = useState<string[]>([]);

  const handleToggle = (id: string) => {
    if (allowMultiple) {
      setOpenIds((prev) =>
        prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
      );
    } else {
      setOpenIds((prev) => (prev.includes(id) ? [] : [id]));
    }
  };

  return (
    <div className="w-full">
      {React.Children.map(children, (child) => {
        if (!React.isValidElement(child)) return child;
        const itemId = child.props.id;
        return React.cloneElement(child, {
          isOpen: openIds.includes(itemId),
          onToggle: () => handleToggle(itemId)
        } as AccordionItemProps);
      })}
    </div>
  );
};
