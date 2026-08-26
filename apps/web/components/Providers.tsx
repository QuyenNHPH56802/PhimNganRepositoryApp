import { NextIntlProvider } from "next-intl";
import { ThemeProvider } from "@/components/ThemeProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NextIntlProvider locale="vi" messages={{}}>
      <ThemeProvider>{children}</ThemeProvider>
    </NextIntlProvider>
  );
}