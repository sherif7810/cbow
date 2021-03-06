import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# Dataset
test_sentence = """When forty winters shall besiege thy brow,
And dig deep trenches in thy beauty's field,
Thy youth's proud livery so gazed on now,
Will be a totter'd weed of small worth held:
Then being asked, where all thy beauty lies,
Where all the treasure of thy lusty days;
To say, within thine own deep sunken eyes,
Were an all-eating shame, and thriftless praise.
How much more praise deserv'd thy beauty's use,
If thou couldst answer 'This fair child of mine
Shall sum my count, and make my old excuse,'
Proving his beauty by succession thine!
This were to be new made when thou art old,
And see thy blood warm when thou feel'st it cold.""".split()

quadgrams = [([test_sentence[i], test_sentence[i + 1],
               test_sentence[i + 3], test_sentence[i + 4]],
              test_sentence[i + 2])
             for i in range(len(test_sentence) - 4)]

vocab = set(test_sentence)
word_to_index = {word: i for i, word in enumerate(vocab)}


class CBoW(torch.jit.ScriptModule):
    """Continuous bag-of-words model."""

    def __init__(self, vocab_size: int, embedding_dim: int, context_size: int):
        super(CBoW, self).__init__()

        self.embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.layer1 = nn.Sequential(
            nn.Linear(context_size * embedding_dim, 128),
            nn.ReLU()
        )
        self.fc2 = nn.Linear(128, vocab_size)

    @torch.jit.script_method
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        embeds = self.embeddings(x).view(1, -1)
        out = self.layer1(embeds)
        out = self.fc2(out)
        log_probs = F.log_softmax(out, dim=1)
        return log_probs


# Model creation
criterion = nn.NLLLoss()
model = CBoW(len(vocab), 50, 4)
optimizer = optim.SGD(model.parameters(), lr=0.001)

# Training
losses = []
for epoch in range(15):
    total_loss = torch.Tensor([0])
    for context, target in quadgrams:
        context_indexes = torch.tensor([word_to_index[w] for w in context],
                                       dtype=torch.long)

        optimizer.zero_grad()
        log_probs = model(context_indexes)

        loss = criterion(
            log_probs,
            torch.tensor([word_to_index[target]], dtype=torch.long))

        loss.backward()
        optimizer.step()

        total_loss += loss
    losses.append(total_loss)

for i, loss in enumerate(losses):
    print("Epoch {}: Loss = {}.".format(i + 1, loss.item()))
