import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-xl">
              N
            </div>
            <span className="font-bold text-2xl">Nia</span>
          </div>
          <div className="flex gap-4">
            <Link href="/login" className="px-6 py-3 text-gray-700 hover:text-gray-900 font-semibold text-lg">
              Sign In
            </Link>
            <Link href="/register" className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-lg">
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-6 py-20 text-center">
        <h1 className="text-6xl font-bold text-gray-900 mb-6">
          Personalized AI Tutoring for Every Student
        </h1>
        <p className="text-2xl text-gray-600 max-w-3xl mx-auto mb-12">
          Safe, COPPA-compliant learning platform that adapts to your child's needs.
          Trusted by parents, loved by students.
        </p>
        <div className="flex gap-6 justify-center">
          <Link
            href="/register"
            className="px-12 py-5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-2xl shadow-lg"
          >
            Start Free Trial
          </Link>
          <Link
            href="#features"
            className="px-12 py-5 bg-white border-2 border-gray-300 hover:border-gray-400 text-gray-900 rounded-xl font-bold text-2xl"
          >
            Learn More
          </Link>
        </div>
      </section>

      {/* Trust Indicators */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-16 grid grid-cols-1 md:grid-cols-3 gap-12">
        <div className="text-center p-8 bg-gray-50 rounded-2xl">
          <div className="text-6xl mb-6">🔒</div>
          <h3 className="font-bold text-2xl mb-4">COPPA Compliant</h3>
          <p className="text-lg text-gray-600">Full parental control and privacy protection</p>
        </div>
        <div className="text-center p-8 bg-gray-50 rounded-2xl">
          <div className="text-6xl mb-6">📚</div>
          <h3 className="font-bold text-2xl mb-4">Curriculum-Based</h3>
          <p className="text-lg text-gray-600">Aligned with Common Core standards</p>
        </div>
        <div className="text-center p-8 bg-gray-50 rounded-2xl">
          <div className="text-6xl mb-6">👥</div>
          <h3 className="font-bold text-2xl mb-4">For All Learners</h3>
          <p className="text-lg text-gray-600">Inclusive design with accessibility features</p>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-5xl font-bold text-center mb-16">How Nia Works</h2>
          <div className="grid md:grid-cols-2 gap-12">
            <div className="bg-white p-10 rounded-2xl shadow-sm border-2">
              <div className="text-4xl font-bold text-blue-600 mb-4">1</div>
              <h3 className="text-3xl font-bold mb-4">Create Your Account</h3>
              <p className="text-xl text-gray-600">Sign up as a parent and add your children's profiles with grade levels and learning preferences.</p>
            </div>
            <div className="bg-white p-10 rounded-2xl shadow-sm border-2">
              <div className="text-4xl font-bold text-blue-600 mb-4">2</div>
              <h3 className="text-3xl font-bold mb-4">Start Learning</h3>
              <p className="text-xl text-gray-600">Students ask questions and receive personalized, curriculum-based responses from Nia.</p>
            </div>
            <div className="bg-white p-10 rounded-2xl shadow-sm border-2">
              <div className="text-4xl font-bold text-blue-600 mb-4">3</div>
              <h3 className="text-3xl font-bold mb-4">Track Progress</h3>
              <p className="text-xl text-gray-600">Parents view detailed insights into topics explored, time spent, and learning progress.</p>
            </div>
            <div className="bg-white p-10 rounded-2xl shadow-sm border-2">
              <div className="text-4xl font-bold text-blue-600 mb-4">4</div>
              <h3 className="text-3xl font-bold mb-4">Stay Informed</h3>
              <p className="text-xl text-gray-600">Receive weekly reports and have full visibility into all conversations.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-5xl font-bold mb-8">Ready to Transform Learning?</h2>
          <p className="text-2xl text-gray-600 mb-12">
            Join families using Nia to make learning engaging and effective.
          </p>
          <Link
            href="/register"
            className="inline-block px-16 py-6 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-2xl shadow-xl"
          >
            Start Free Trial
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-gray-50 py-12">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-600">
          <p className="text-lg">&copy; 2024 Nia Learning Assistant. All rights reserved.</p>
          <div className="flex gap-8 justify-center mt-6 text-lg">
            <Link href="/privacy" className="hover:text-gray-900 font-semibold">Privacy Policy</Link>
            <Link href="/terms" className="hover:text-gray-900 font-semibold">Terms of Service</Link>
            <Link href="/contact" className="hover:text-gray-900 font-semibold">Contact</Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
