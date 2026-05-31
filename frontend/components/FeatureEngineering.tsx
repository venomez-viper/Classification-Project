"use client";
import { motion } from "framer-motion";
import { Filter, Hash, Layers, BarChart, FileText } from "lucide-react";
import { GlowCard } from "@/components/ui/spotlight-card";
import { TextScramble } from "@/components/ui/text-scramble";

const FEATURES = [
  {
    icon: FileText,
    title: "Text Concatenation",
    glowColor: "red" as const,
    description:
      "For Task 1 we joined LongProfile, SegmentName, and SegmentDescription into one big string per row. LongProfile has the full company operations description and gave us the biggest accuracy boost.",
    code: 'df["text"] = df["LongProfile"] + " " + df["SegmentName"] + " " + df["SegmentDescription"]',
  },
  {
    icon: Filter,
    title: "Stop Word Removal",
    glowColor: "blue" as const,
    description:
      "We used sklearn's built-in English stop word list to drop common words like the, and, is. These appear in every document so they carry zero predictive value for industry classification.",
    code: 'TfidfVectorizer(stop_words="english")',
  },
  {
    icon: Hash,
    title: "Bigram Tokenization",
    glowColor: "orange" as const,
    description:
      "Single words like banking are vague. Bigrams like investment banking or cloud computing are far more specific. We used ngram_range=(1,2) to capture both single words and meaningful two-word phrases.",
    code: 'TfidfVectorizer(ngram_range=(1, 2))',
  },
  {
    icon: Layers,
    title: "Sublinear TF Scaling",
    glowColor: "green" as const,
    description:
      "LongProfile text is very long. Without scaling, companies with longer profiles dominate the vector space. sublinear_tf=True replaces raw count with 1+log(tf) which levels the playing field.",
    code: 'TfidfVectorizer(sublinear_tf=True)',
  },
  {
    icon: BarChart,
    title: "Feature Ceiling",
    glowColor: "purple" as const,
    description:
      "Task 1 uses 60,000 features because the full LongProfile vocabulary is huge. Task 2 only gets 10,000 since it only reads SegmentName and SegmentDescription which are much shorter texts.",
    code: 'TfidfVectorizer(max_features=60000)  # Task 1\nTfidfVectorizer(max_features=10000)  # Task 2',
  },
];

export default function FeatureEngineering() {
  return (
    <section id="features" className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <TextScramble as="p" speed={0.02} duration={0.7} className="text-red-500 text-sm font-semibold uppercase tracking-widest mb-3">
            Feature Engineering
          </TextScramble>
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-5">
            How We Turned Text Into Numbers
          </h2>
          <p className="text-white/50 text-lg max-w-2xl mx-auto">
            Machine learning models cannot read text. Everything has to become a number. Here is
            every design decision we made to get from raw company descriptions to a sparse feature matrix.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-5 mb-10 items-stretch">
          {FEATURES.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="h-full"
            >
              <GlowCard glowColor={f.glowColor} className="h-full flex flex-col">
                <div className="flex items-center gap-3 mb-3 text-white/80">
                  <f.icon className="w-5 h-5" />
                  <TextScramble as="span" speed={0.02} duration={0.5} className="font-semibold text-base text-white">
                    {f.title}
                  </TextScramble>
                </div>
                <p className="text-white/55 text-sm leading-relaxed flex-1 mb-4">{f.description}</p>
                <code className="block text-xs font-mono bg-black/50 text-white/50 px-3 py-2.5 rounded-lg whitespace-pre overflow-x-auto mt-auto">
                  {f.code}
                </code>
              </GlowCard>
            </motion.div>
          ))}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <GlowCard glowColor="red" className="text-center">
            <p className="text-white/40 text-sm mb-2">Final Output</p>
            <p className="text-white font-mono text-base">
              Task 1: <span className="text-red-400">53,587 x 60,000</span> sparse matrix
              <span className="text-white/30 mx-3">|</span>
              Task 2: <span className="text-blue-400">~47,000 x 10,000</span> sparse matrix
            </p>
            <p className="text-white/30 text-xs mt-2">
              Stored as compressed scipy.sparse CSR format. No dense arrays. No RAM explosion.
            </p>
          </GlowCard>
        </motion.div>
      </div>
    </section>
  );
}
