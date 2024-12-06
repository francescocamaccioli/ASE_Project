import './globals.css';
import Navbar from '../components/Navbar';

export const metadata = {
  title: 'Gatcha Collection App',
};

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <Navbar />
        <div className="container p-4 mx-auto">{children}</div>
      </body>
    </html>
  );
}