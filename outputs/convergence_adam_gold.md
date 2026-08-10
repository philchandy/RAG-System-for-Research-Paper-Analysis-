# On the Convergence of Adam and Beyond

## problem
- Several popular adaptive stochastic optimization methods used to train deep networks, including RMSPROP, ADAM, ADADELTA, and NADAM, scale gradient updates using exponential moving averages of squared past gradients, but have been empirically observed to fail to converge to an optimal solution or critical point in some settings, such as learning with large output spaces.
- The paper investigates the cause of these failures and identifies a flaw in the original convergence proof of ADAM given by Kingma & Ba (2015).

## method
- The authors construct explicit simple convex optimization examples where ADAM and RMSPROP provably fail to converge to the optimal solution, showing the flaw stems from the "learning rate" quantity (related to the inverse square root of the exponential moving average) becoming non-monotonic/indefinite over time, unlike SGD and ADAGRAD.
- They prove that for any constant β1, β2 with β1 < √β2 (the typical practical setting), there exists an online or stochastic convex optimization problem where ADAM has non-zero average regret asymptotically.
- Based on this diagnosis, they propose AMSGRAD, a new variant that maintains the maximum of all past squared-gradient averages (v̂t = max(v̂t−1, vt)) and uses this running maximum to normalize the update, guaranteeing a non-increasing learning rate while preserving ADAM's practical time and space complexity, and provide a convergence/regret bound for it in the convex setting.

## dataset
- Synthetic online and stochastic convex optimization problems (hand-constructed counterexample sequences of linear functions) used to demonstrate ADAM's non-convergence.
- MNIST (784-dimensional image vectors, 10 class labels) used for logistic regression and a 1-hidden-layer feedforward neural network with 100 ReLU units.
- CIFAR-10 (60,000 labeled 32×32 images) used with "CIFARNET," a convolutional neural network with 2 convolutional layers (64 channels, 6×6 kernels), 2×2 max pooling, and 2 fully connected layers (sizes 384 and 192) with dropout (keep probability 0.5).

## results
- On the constructed synthetic convex problems, ADAM's average regret does not converge to 0 and its iterate converges to the most suboptimal point in the feasible set, while AMSGRAD's average regret converges to 0 and its iterate converges to the optimal solution, in both the online and stochastic settings.
- On MNIST logistic regression, AMSGRAD achieves better train and test loss than ADAM and is more robust to changes in hyperparameters.
- On the CIFAR-10 CIFARNET experiment, AMSGRAD performs considerably better than ADAM on training loss and accuracy, and this improvement also translates to better test loss.

## limitations
- The convergence/regret analysis provided for AMSGRAD (and the ADAMNC variant) is developed for the convex setting; the paper does not provide a general convergence guarantee for nonconvex problems like deep neural network training.
- The theoretical non-convergence results are proven explicitly for ADAM and RMSPROP with constant β1; the paper states the analysis "easily extends" to ADADELTA, NADAM, and decreasing-β1 schedules but explicitly omits carrying out this general analysis for the sake of clarity.
- The empirical evaluation of AMSGRAD on neural networks is described by the authors as a "preliminary empirical study," limited to logistic regression, a small feedforward network, and one CNN architecture on MNIST/CIFAR-10.

## follow_up_questions

Answerable from the paper:
- Q: What new algorithm does the paper propose to fix ADAM's convergence issues?
  A: AMSGRAD.
- Q: What key modification distinguishes AMSGRAD from ADAM?
  A: AMSGRAD maintains the maximum of all past vt values (v̂t = max(v̂t−1, vt)) and normalizes the update using this running maximum instead of vt directly, ensuring a non-increasing learning rate.
- Q: What datasets were used in the neural network experiments?
  A: MNIST (logistic regression and a 1-hidden-layer feedforward network) and CIFAR-10 (using the CIFARNET CNN).
- Q: What values of β1 and β2 are typically recommended for ADAM in practice?
  A: β1 = 0.9 and β2 = 0.999.
- Q: Under what condition on β1 and β2 does the paper prove ADAM has non-zero average regret asymptotically?
  A: For any constant β1, β2 ∈ [0,1) such that β1 < √β2.

Not answered in the paper:
- Q: What GPU or hardware was used to run the experiments?
  A: Not mentioned in the paper.
- Q: How does AMSGRAD perform on training large language models?
  A: Not studied — the paper only evaluates logistic regression, a small feedforward network, and CIFARNET on MNIST/CIFAR-10.
- Q: What is AMSGRAD's convergence guarantee in the general nonconvex setting?
  A: Not provided — the paper's convergence analysis covers the convex setting only.
