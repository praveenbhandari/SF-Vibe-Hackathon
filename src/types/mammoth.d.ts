declare module 'mammoth' {
  interface ConvertToHtmlOptions {
    convertImage?: (image: any) => any;
    ignoreEmptyParagraphs?: boolean;
    includeDefaultStyleMap?: boolean;
    includeEmbeddedStyleMap?: boolean;
    styleMap?: string[];
    transformDocument?: (document: any) => any;
  }

  interface ConvertToMarkdownOptions {
    convertImage?: (image: any) => any;
    ignoreEmptyParagraphs?: boolean;
    styleMap?: string[];
    transformDocument?: (document: any) => any;
  }

  interface ConvertResult {
    value: string;
    messages: any[];
  }

  export function convertToHtml(
    input: { buffer: ArrayBuffer } | { path: string },
    options?: ConvertToHtmlOptions
  ): Promise<ConvertResult>;

  export function convertToMarkdown(
    input: { buffer: ArrayBuffer } | { path: string },
    options?: ConvertToMarkdownOptions
  ): Promise<ConvertResult>;

  export function extractRawText(
    input: { buffer: ArrayBuffer } | { path: string }
  ): Promise<ConvertResult>;
}