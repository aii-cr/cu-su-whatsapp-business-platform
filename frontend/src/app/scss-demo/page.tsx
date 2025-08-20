/**
 * Demo page showcasing SCSS + Tailwind integration
 */

import { EnhancedButton } from '@/components/ui/EnhancedButton';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { 
  MessageCircle, 
  Send, 
  Heart, 
  Star, 
  Zap, 
  Sparkles,
  Phone,
  Mail,
  Settings
} from 'lucide-react';

export default function SCSSDemoPage() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-foreground">
            SCSS + Tailwind Integration Demo
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            This page demonstrates how SCSS and Tailwind CSS work together seamlessly.
            SCSS handles complex styling while Tailwind manages layout and responsive design.
          </p>
        </div>

        {/* Enhanced Button Showcase */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Enhanced Buttons with SCSS Effects</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Gradient Effect</h3>
              <EnhancedButton effect="gradient" icon={<Sparkles className="w-4 h-4" />}>
                Gradient Button
              </EnhancedButton>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Neon Glow</h3>
              <EnhancedButton effect="neon" variant="primary" icon={<Zap className="w-4 h-4" />}>
                Neon Button
              </EnhancedButton>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-medium">3D Effect</h3>
              <EnhancedButton effect="threeD" variant="secondary" icon={<Star className="w-4 h-4" />}>
                3D Button
              </EnhancedButton>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Ripple Effect</h3>
              <EnhancedButton effect="ripple" variant="outline" icon={<Heart className="w-4 h-4" />}>
                Ripple Button
              </EnhancedButton>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-medium">WhatsApp Style</h3>
              <EnhancedButton effect="whatsapp" icon={<MessageCircle className="w-4 h-4" />}>
                Send Message
              </EnhancedButton>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Loading State</h3>
              <EnhancedButton effect="gradient" loading>
                Loading...
              </EnhancedButton>
            </div>
          </div>
        </Card>

        {/* Comparison: Tailwind vs SCSS */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card className="p-6">
            <h2 className="text-2xl font-semibold mb-6">Tailwind Only</h2>
            <div className="space-y-4">
              <Button variant="default" icon={<Phone className="w-4 h-4" />}>
                Call Now
              </Button>
              <Button variant="outline" icon={<Mail className="w-4 h-4" />}>
                Send Email
              </Button>
              <Button variant="secondary" icon={<Settings className="w-4 h-4" />}>
                Settings
              </Button>
              <p className="text-sm text-muted-foreground mt-4">
                These buttons use only Tailwind classes for styling.
              </p>
            </div>
          </Card>
          
          <Card className="p-6">
            <h2 className="text-2xl font-semibold mb-6">SCSS + Tailwind</h2>
            <div className="space-y-4">
              <EnhancedButton effect="gradient" icon={<Phone className="w-4 h-4" />}>
                Call Now
              </EnhancedButton>
              <EnhancedButton effect="neon" variant="outline" icon={<Mail className="w-4 h-4" />}>
                Send Email
              </EnhancedButton>
              <EnhancedButton effect="threeD" variant="secondary" icon={<Settings className="w-4 h-4" />}>
                Settings
              </EnhancedButton>
              <p className="text-sm text-muted-foreground mt-4">
                These buttons combine Tailwind for layout with SCSS for complex effects.
              </p>
            </div>
          </Card>
        </div>

        {/* WhatsApp Chat Demo */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">WhatsApp-Style Chat Interface</h2>
          <div className="chat-container h-96 border rounded-lg">
            <div className="chat-header">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                  <MessageCircle className="w-5 h-5 text-primary-foreground" />
                </div>
                <div>
                  <h3 className="font-semibold">Customer Support</h3>
                  <p className="text-sm text-muted-foreground">Online</p>
                </div>
              </div>
              <Badge variant="secondary" className="bg-success text-white">
                Active
              </Badge>
            </div>
            
            <div className="chat-messages">
              <div className="message-bubble">
                <p className="chat-message">Hello! How can I help you today?</p>
                <p className="chat-timestamp">10:30 AM</p>
              </div>
              
              <div className="message-bubble own-message">
                <p className="chat-message">Hi! I need help with my order.</p>
                <p className="chat-timestamp">10:32 AM</p>
              </div>
              
              <div className="message-bubble">
                <p className="chat-message">Of course! I'd be happy to help. Can you provide your order number?</p>
                <p className="chat-timestamp">10:33 AM</p>
              </div>
            </div>
            
            <div className="chat-input-container">
              <input 
                type="text" 
                placeholder="Type your message..." 
                className="chat-input"
              />
              <EnhancedButton effect="whatsapp" icon={<Send className="w-4 h-4" />} size="sm">
                Send
              </EnhancedButton>
            </div>
          </div>
        </Card>

        {/* SCSS Utilities Demo */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">SCSS Utility Classes</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Glass Morphism</h3>
              <div className="glass p-6 rounded-lg">
                <p className="text-foreground">This card uses the glass effect from SCSS mixins.</p>
              </div>
              <div className="glass-light p-6 rounded-lg">
                <p className="text-foreground">Light glass effect</p>
              </div>
              <div className="glass-heavy p-6 rounded-lg">
                <p className="text-foreground">Heavy glass effect</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <h3 className="text-lg font-medium">Loading States</h3>
              <div className="skeleton h-4 w-full rounded"></div>
              <div className="skeleton h-4 w-3/4 rounded"></div>
              <div className="skeleton h-4 w-1/2 rounded"></div>
              <div className="skeleton h-20 w-full rounded"></div>
            </div>
          </div>
        </Card>

        {/* Animation Showcase */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">SCSS Animations</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="animate-fade-in p-4 border rounded-lg text-center">
              <p>Fade In</p>
            </div>
            <div className="animate-slide-up p-4 border rounded-lg text-center">
              <p>Slide Up</p>
            </div>
            <div className="animate-scale-in p-4 border rounded-lg text-center">
              <p>Scale In</p>
            </div>
            <div className="animate-bounce p-4 border rounded-lg text-center">
              <p>Bounce</p>
            </div>
          </div>
        </Card>

        {/* Best Practices */}
        <Card className="p-6">
          <h2 className="text-2xl font-semibold mb-6">Best Practices</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-medium mb-3">✅ Do's</h3>
              <ul className="space-y-2 text-sm">
                <li>• Use Tailwind for layout, spacing, and responsive design</li>
                <li>• Use SCSS modules for complex component-specific styling</li>
                <li>• Keep SCSS variables in sync with Tailwind design tokens</li>
                <li>• Use @apply sparingly for repetitive utility combinations</li>
                <li>• Create reusable SCSS mixins for complex patterns</li>
              </ul>
            </div>
            <div>
              <h3 className="text-lg font-medium mb-3">❌ Don'ts</h3>
              <ul className="space-y-2 text-sm">
                <li>• Don't duplicate Tailwind utilities in SCSS</li>
                <li>• Don't create global SCSS styles for components</li>
                <li>• Don't override Tailwind's responsive breakpoints</li>
                <li>• Don't use SCSS for simple layout tasks</li>
                <li>• Don't forget to use CSS modules to prevent style leaks</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
